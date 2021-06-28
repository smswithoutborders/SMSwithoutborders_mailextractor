#!/usr/bin/python3

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
from tqdm import tqdm
from email.parser import HeaderParser
from datastore import Datastore

CONFIGS = configparser.ConfigParser(interpolation=None)
PATH_CONFIG_FILE = os.path.join(os.path.dirname(__file__), '', 'config.ini')
CONFIGS.read(PATH_CONFIG_FILE)

def get_mails():
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
    # max_counter = int(sys.argv[1])
    '''
    ['Return-Path', 'Delivered-To', 'Received', 'Received', 'Received', 'Received', 'Received', 'DKIM-Signature', 'X-Google-DKIM-Signature', 'X-Gm-Message-State', 'X-Google-Smtp-Source', 'MIME-Version', 'X-Received', 'Date', 'Reply-To', 'Message-ID', 'Subject', 'From', 'To', 'Cc', 'Content-Type', 'X-NCJF-Result', 'X-NCJF-Version', 'Authentication-Results']
    '''
    msgs = msgnums[0].split()
    for i in tqdm(range(len(msgs)), "extracting..."):
        num = msgs[i]
        mtyp, msg = imap.fetch(num, STANDARDS)
        data=msg[0][CONTENT_INDEX]
        msg = email.message_from_bytes(data)
        # print(msg.keys())
        # datastore = Datastore()
        _id = msg['Message-ID']
        _from = msg['From']
        To = msg['To']
        Subject = msg['Subject']
        reply_to = msg['Reply-To']
        cc = msg['Cc']
        date=msg['Date']
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
        '''
        print(f"ID: {msg['Message-ID']}")
        print(f"From: {msg['From']}")
        print(f"Reply-To: {msg['Reply-To']}")
        print(f"To: {msg['To']}")
        print(f"Cc: {msg['Cc']}")
        print(f"Subject: {msg['Subject']}") 
        print(f"Date: {msg['Date']}") 
        print(f"Encoding: {encoding}")
        print(f"Encodings: {encodings}")
        print(f"Content-Transfer-Encoding: {content_transfer_encoding}")
        print(f"Body - snippet: {Body[:40]}", end="\n\n")
        '''

        datastore = Datastore()
        try:
            insert_status = datastore.new_message( \
                    _id = _id, \
                    _from = _from, \
                    to = To, \
                    subject = Subject, \
                    reply_to = reply_to, \
                    cc = cc, \
                    date = date, \
                    encoding = encoding, \
                    content_transfer_encoding = content_transfer_encoding, \
                    body = Body)
        except Exception as error:
            print(error)
    imap.close()

if __name__ == "__main__":
    import start_routines
    start_routines.sr_database_checks()
    get_mails()

