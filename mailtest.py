from __future__ import print_function
import asyncore, collections, json, smtpd, sys, threading, time
from wsgiref.simple_server import make_server, WSGIRequestHandler, WSGIServer
import bottle

__version__ = '1.1.0'


try:
  import sendgrid
except ImportError:  
  sendgrid = None


class _SMTPServer(smtpd.SMTPServer):

  def process_message(self, peer, mailfrom, rcpttos, data):
    email = Email(frm=mailfrom, to=rcpttos, msg=data)
    for callback in self.callbacks.values():
      callback(email)

_smtp_servers = {}


class Server(object):

  def __init__(self, smtp_port=1025, sendgrid_port=None):
    self._smtp_port = smtp_port
    self._sendgrid_port = sendgrid_port
    self._sendgrid_server = None
    self.emails = []
    if sendgrid_port:
      self._sendgrid_app = app = bottle.Bottle()

      @app.get('/v3/templates')
      def templates():
        return {'templates': []}
      
      @app.post('/v3/mail/send')
      def send():
        d = bottle.request.json
        for p in d['personalizations']:
          email = Email(frm=d['from']['email'], to=[addr['email'] for addr in p['to']], msg=json.dumps(p, indent=2))
          self.emails.append(email)
        return {}
      

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
    def f():
      self._sendgrid_server = make_server('localhost', self._sendgrid_port, self._sendgrid_app, WSGIServer, WSGIRequestHandler)
      self._sendgrid_server.serve_forever(poll_interval=.1)
    t = threading.Thread(target=f)
    t.start()
    time.sleep(.1)
    

  def __enter__(self):
    if self._smtp_port: self._start_smtp_server()
    if self._sendgrid_port: self._start_sendgrid_server()
    return self

  def __exit__(self, type, value, tb):
    if self._smtp_port:
      del _smtp_servers[self._smtp_port].callbacks[id(self)]
    if self._sendgrid_server:
      #print('closing', self._sendgrid_server)
      self._sendgrid_server.shutdown()
      self._sendgrid_server.server_close()


Email = collections.namedtuple('Email', ['frm','to','msg'])



