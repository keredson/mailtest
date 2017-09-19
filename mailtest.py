from __future__ import print_function
import asyncore, collections, email, json, smtpd, sys, threading, time
from wsgiref.simple_server import make_server, WSGIRequestHandler, WSGIServer
import bottle

__version__ = '1.1.3'


try:
  import sendgrid
except ImportError:  
  sendgrid = None


class _SMTPServer(smtpd.SMTPServer):

  def process_message(self, peer, mailfrom, rcpttos, data):
    b = email.message_from_string(data)
    body_parts = []
    if b.is_multipart():
      for part in b.walk():
        ctype = part.get_content_type()
        cdispo = str(part.get('Content-Disposition'))
        if ctype in ('text/plain','text/html') and 'attachment' not in cdispo:
          body_parts.append(part.get_payload(decode=True).decode())
    else:
      body_parts = [b.get_payload(decode=True).decode()]
    e = Email(frm=mailfrom, to=rcpttos, raw=data, msg='\n'.join(body_parts))
    for callback in self.callbacks.values():
      callback(e)

_smtp_servers = {}

class _SendgridServer(object):
  def __init__(self, port):
    self.port = port
    self.app = app = bottle.Bottle()

    @app.get('/v3/templates')
    def templates():
      return {'templates': []}
    
    @app.post('/v3/mail/send')
    def send():
      d = bottle.request.json
      for p in d['personalizations']:
        msg = json.dumps(p, indent=2)
        email = Email(frm=d['from']['email'], to=[addr['email'] for addr in p['to']], msg=msg, raw=msg)
        for callback in self.callbacks.values():
          callback(email)
      return {}

  def start(self):
    def f():
      self._sendgrid_server = make_server('localhost', self.port, self.app, WSGIServer, WSGIRequestHandler)
      self._sendgrid_server.serve_forever()
    t = threading.Thread(target=f)
    t.daemon = True
    t.start()
    time.sleep(.1)

_sendgrid_servers = {}


class Server(object):

  def __init__(self, smtp_port=1025, sendgrid_port=None):
    self._smtp_port = smtp_port
    self._sendgrid_port = sendgrid_port
    self._sendgrid_server = None
    self.emails = []
      

  def _callback(self, email):
    self.emails.append(email)
  
  def _start_smtp_server(self):
    _smtp_server = _smtp_servers.get(self._smtp_port)
    if not _smtp_server:
      if sys.version_info[0] < 3:
        _smtp_server = _SMTPServer(('localhost', self._smtp_port), None)
      else:
        _smtp_server = _SMTPServer(('localhost', self._smtp_port), None, decode_data=True)
      _smtp_servers[self._smtp_port] = _smtp_server
      _smtp_server.callbacks = {}
      t = threading.Thread(target=asyncore.loop)
      t.daemon = True
      t.start()
    _smtp_server.callbacks[id(self)] = self._callback
  
  def _start_sendgrid_server(self):
    server = _sendgrid_servers.get(self._sendgrid_port)
    if not server:
      _sendgrid_servers[self._sendgrid_port] = server = _SendgridServer(self._sendgrid_port)
      server.callbacks = {}
      server.start()
    server.callbacks[id(self)] = self._callback

  def __enter__(self):
    if self._smtp_port: self._start_smtp_server()
    if self._sendgrid_port: self._start_sendgrid_server()
    return self

  def __exit__(self, type, value, tb):
    if self._smtp_port:
      del _smtp_servers[self._smtp_port].callbacks[id(self)]
    if self._sendgrid_port:
      del _sendgrid_servers[self._sendgrid_port].callbacks[id(self)]


Email = collections.namedtuple('Email', ['frm','to','msg','raw'])



