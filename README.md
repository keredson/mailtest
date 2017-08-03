# MailTest
MailTest is a Python unittesting library that for code that sends email.  It starts a local SMTP server inside a Python `with` block, and captures all the email sent to it.  These emails can then be read within the block.

Example:

```
with mailtest.Server() as mt:
    send_welcome_email()
    assert len(mt.emails) == 1
```

## Install
```
pip3 install mailtest
```

## Configuration
Configuration is done via kwargs to `mailtest.Server()`.  Options:
- `smtp_port` (defaults to 1025)
- `sendgrid_port` (TODO)

## Speed
MailTest can test receive approx. 4000 emails/second on an Intel(R) Core(TM) i5-7260U CPU @ 2.20GHz.

## Testing
```
$ python2 test.py 
..
----------------------------------------------------------------------
Ran 2 tests in 0.269s

OK
```
```
$ python3 test.py 
..
----------------------------------------------------------------------
Ran 2 tests in 0.543s

OK
```
