#!/usr/bin/python

''' resources
- https://docs.python.org/3/library/imaplib.html
- https://datatracker.ietf.org/doc/html/rfc3501#section-6.4.5
- https://docs.python.org/3/library/email.compat32-message.html#email.message.Message
'''

import imaplib
import sys
import os
import configparser
import base64
import email
from email.parser import HeaderParser

CONFIGS = configparser.ConfigParser(interpolation=None)
PATH_CONFIG_FILE = os.path.join(os.path.dirname(__file__), '', 'config.ini')
CONFIGS.read(PATH_CONFIG_FILE)

imap_host = CONFIGS['IMAP']['HOST']
imap_user = CONFIGS['IMAP']['USER']
imap_pass = CONFIGS['IMAP']['PASSWORD']

imap = imaplib.IMAP4_SSL(imap_host)
imap.login(imap_user, imap_pass)

imap.select('Inbox')

typ, msgnums = imap.search(None, 'ALL')

CONTENT_INDEX=1
STANDARDS='(RFC822)'
parser = HeaderParser()
for num in msgnums[0].split():
    mtyp, msg = imap.fetch(num, STANDARDS)
    header_data=msg[0][CONTENT_INDEX]
    msg = email.message_from_bytes(header_data)

    print(f"From: {msg['From']}")
    print(f"To: {msg['To']}")
    print(f"Subject: {msg['Subject']}")
    # print(f"Content-Type {msg['Content-Type']}")

    for part in msg.walk():
        if part.get_content_type() == "text/plain":
            # TODO: get encoding from part.get_charset()
            print(str(base64.b64decode(part.get_payload()), 'utf-8'))
    break
    

# for num in msgnums
'''
for num in data[0].split():
    tmp, data = imap.fetch(num, '(RFC822)')
    print('Message: {0}\n'.format(num))
    pprint.pprint(data[0][1])
    break
'''
imap.close()
