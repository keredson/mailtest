import smtplib, unittest
import mailtest

class TestMailTest(unittest.TestCase):

  def test_smtp(self):
    with mailtest.Server(smtp_port=1025) as s:
      sender = smtplib.SMTP('localhost', 1025)
      sender.sendmail('author@example.com', ['recipient@example.com'], 'hi')
      self.assertEqual(len(s.emails), 1)
      self.assertEqual(s.emails[0].frm, 'author@example.com')
      self.assertEqual(s.emails[0].to, ['recipient@example.com'])
      self.assertEqual(s.emails[0].msg, 'hi')

  def test_mass_email(self):
    with mailtest.Server(smtp_port=1025) as s:
      sender = smtplib.SMTP('localhost', 1025)
      c = 1000 # ~0.240s
      for i in range(c):
        sender.sendmail('author@example.com', ['recipient@example.com'], 'msg #%i' % i)
      self.assertEqual(len(s.emails), c)


if __name__ == '__main__':
    unittest.main()

