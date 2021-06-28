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
# from datastore import Datastore

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

msg_counter=0
max_counter = int(sys.argv[1])
for num in msgnums[0].split():
    mtyp, msg = imap.fetch(num, STANDARDS)
    data=msg[0][CONTENT_INDEX]
    msg = email.message_from_bytes(data)
    # print(msg.keys())
    # datastore = Datastore()
    _id = msg['Message-ID']
    _from = msg['From']
    To = msg['To']
    Subject = msg['Subject']
    encoding=None
    encodings=[]
    content_transfer_encoding=None
    Body=None

    for part in msg.walk():
        if part.get_content_type() == "text/plain":
            encoding = part.get_charsets()[0]
            encodings = part.get_charsets()
            # print(str(base64.b64decode(part.get_payload()), encoding))
            # print(part.get_payload())
            content_transfer_encoding=part['Content-Transfer-Encoding']
            Body=part.get_payload()

    '''
    if msg['Message-ID'] == '<0000000000008af50105c51941cc@google.com>':
        print(data)
    '''
    print(f"ID: {msg['Message-ID']}")
    print(f"From: {msg['From']}")
    print(f"To: {msg['To']}")
    print(f"Subject: {msg['Subject']}") 
    print(f"Encoding: {encoding}")
    print(f"Encodings: {encodings}")
    print(f"Content-Transfer-Encoding: {content_transfer_encoding}")
    print(f"Body - snippet: {Body[:40]}", end="\n\n")

    datastore = Datastore()
    try:
        insert_status = datastore.new_message( \
                _id = _id, \
                _from = _from, \
                to = to, \
                subject = subject, \
                reply_to = reply_to, \
                cc = cc, \
                date = date, \
                encoding = encoding, \
                content_transfer_encoding = content_transfer_encoding, \
                body = body)
    except Exception as error:
        print(error)
imap.close()
