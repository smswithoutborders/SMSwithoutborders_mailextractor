#!/usr/bin/python

import imaplib
import sys
import os
import configparser
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

HEADER_INDEX=1
parser = HeaderParser()
for num in msgnums[0].split():
    mtyp, msg = imap.fetch(num, '(BODY[HEADER])')
    # print(type(msg[0][HEADER_INDEX]))
    # msg = msg[0][1].decode('utf-8')
    header_data=msg[0][HEADER_INDEX]
    msg = parser.parsestr(header_data.decode('utf-8'))
    # print(msg.keys())
    print(f"From {msg['From']}")
    print(f"To {msg['To']}")
    print(f"Subject {msg['Subject']}")
    print(f"Content-Type {msg['Content-Type']}")
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
