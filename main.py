#!/usr/bin/python

import imaplib
import pprint
import sys
import configparser

CONFIGS = configparser.ConfigParser(interpolation=None)
PATH_CONFIG_FILE = os.path.join(os.path.dirname(__file__), '', 'config.ini')

imap_host = CONFIGS['IMAP_HOST']
imap_user = CONFIGS['IMAP_USER']
imap_pass = CONFIGS['IMAP_PASSWORD']

imap = imaplib.IMAP4_SSL(imap_host)
imap.login(imap_user, imap_pass)

imap.select('Inbox')

typ, msgnums = imap.search(None, 'ALL')
# print(imap.search(None, 'ALL'))
# print(msgnums)
print(type(msgnums))
for num in msgnums[0].split():
    mtyp, msg = imap.fetch(num, '(BODY[HEADER])')
    print(msg, end="\n\n")
    

# for num in msgnums
'''
for num in data[0].split():
    tmp, data = imap.fetch(num, '(RFC822)')
    print('Message: {0}\n'.format(num))
    pprint.pprint(data[0][1])
    break
'''
imap.close()
