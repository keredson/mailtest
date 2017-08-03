import smtplib, unittest
import mailtest

try:
  import sendgrid
except ImportError:  
  sendgrid = None


class TestMailTest(unittest.TestCase):

  def test_smtp(self):
    with mailtest.Server(smtp_port=1025) as s:
      sender = smtplib.SMTP('localhost', 1025)
      sender.sendmail('author@example.com', ['recipient@example.com'], 'hi')
      sender.close()
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
      sender.close()
      self.assertEqual(len(s.emails), c)
  
  if sendgrid:
    def test_sendgrid(self):
      with mailtest.Server(sendgrid_port=1080) as s:
        sg = sendgrid.SendGridAPIClient(apikey='any', host='http://localhost:1080')
        sg.client.templates.get()
        mail = sendgrid.helpers.mail.Mail()
        mail.from_email = sendgrid.helpers.mail.Email('author@example.com', 'Author Name')
        mail.subject = 'test email'
        mail.template_id = '12345'
        for i in range(5):
          person = sendgrid.helpers.mail.Personalization()
          person.add_to(sendgrid.helpers.mail.Email('recipient%i@example.com' % i, 'Recipient #%i' % i))
          #person.add_substitution(Substitution(unsubscribe_path, user.unsubscribe_path()))
          #person.add_custom_arg(CustomArg("user_id", str(user.id)))
          mail.add_personalization(person)
        body = mail.get()
        sg.client.mail.send.post(request_body=body)
        self.assertEqual(len(s.emails), 5)
        self.assertEqual(s.emails[0].frm, 'author@example.com')
        self.assertEqual(s.emails[0].to, ['recipient0@example.com'])
#        self.assertEqual(s.emails[0].msg, 'hi')



if __name__ == '__main__':
    unittest.main()

