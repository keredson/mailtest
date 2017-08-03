import asyncore, collections, smtpd, sys, threading


__version__ = '1.0.0'

class _SMTPServer(smtpd.SMTPServer):

  def process_message(self, peer, mailfrom, rcpttos, data):
    email = Email(frm=mailfrom, to=rcpttos, msg=data)
    self.callback(email)


class Server(object):

  def __init__(self, smtp_port=1025):
    self._smtp_port = smtp_port
    self.emails = []

  def _callback(self, email):
    self.emails.append(email)

  def __enter__(self):
    if sys.version_info[0] < 3:
      self.server = _SMTPServer(('localhost', self._smtp_port), None)
    else:
      self.server = _SMTPServer(('localhost', self._smtp_port), None, decode_data=True)
    self.server.callback = self._callback
    t = threading.Thread(target=asyncore.loop)
    t.start()
    return self

  def __exit__(self, type, value, tb):
    self.server.close()


Email = collections.namedtuple('Email', ['frm','to','msg'])
