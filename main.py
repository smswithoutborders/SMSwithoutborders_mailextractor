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
import requests
import re
from tqdm import tqdm
from email.parser import HeaderParser
from datastore import Datastore

CONFIGS = configparser.ConfigParser(interpolation=None)
PATH_CONFIG_FILE = os.path.join(os.path.dirname(__file__), '', 'config.ini')
CONFIGS.read(PATH_CONFIG_FILE)

def check_ssl():
    return os.path.isfile( CONFIGS["SSL"]["KEY"] ) and os.path.isfile(CONFIGS["SSL"]["CRT"])

'''
- todo: remove copied message body - significantly reduces the sizes of some emails
'''

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
    messages = []
    for i in tqdm(range(len(msgs)), "extracting..."):
        num = msgs[i]
        mtyp, msg = imap.fetch(num, STANDARDS)
        data=msg[0][CONTENT_INDEX]
        msg = email.message_from_bytes(data)
        # print(msg.keys())
        # datastore = Datastore()
        ID = msg['Message-ID']
        From = msg['From']
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
                Body=part.get_payload(decode=True)

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
            # store_messages( ID=ID, From=From, To=To, Subject=Subject, reply_to=reply_to, cc=cc, date=date, encoding=encoding, content_transfer_encoding=content_transfer_encoding, Body=Body)
            pass
        except Exception as error:
            print(error)
        else:
            message = {}
            message["from"] = From
            message["to"] = To
            message["subject"] = Subject
            message["body"] = reply_parser(bytes.decode(Body))
            message["reply_to"] = reply_to
            message["cc"] = cc
            message["content_transfer_encoding"] = content_transfer_encoding
            message["encoding"] = encoding

            messages.append(message)
            break
    imap.close()
    return messages

def store_messages( ID, From, To, Subject, reply_to, date, encoding, Body, cc=None, content_transfer_encoding=None):
    datastore = Datastore()
    try:
        insert_status = datastore.new_message( \
                _id = ID, \
                _from = From, \
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
    else:
        return True
    return False

def transmit_messages(messages):
    # TODO: email should be saved for processing
    # TODO: forward email to messaging priority
    # pass
    '''
    - send associated message to router
    '''
    
    # TODO: check for character limits
    request=None
    '''
    if content_transfer_encoding == 'base64':
        Body = base64.b64decode(Body)
    '''
    iter_count=1
    for message in messages:
        print(f"> Transmitting {iter_count} of {len(messages)}")
        try:
            if check_ssl():
                # request = requests.post(CONFIGS['TWILIO']['SEND_URL'], json={"number":sys.argv[1], "text":Body}, cert=(CONFIGS["SSL"]["CRT"], CONFIGS["SSL"]["KEY"]))
                request = requests.post(CONFIGS['TWILIO']['SEND_URL'], json={"number":sys.argv[1], "text":message['body'][:1600]}, cert=(CONFIGS["SSL"]["CRT"], CONFIGS["SSL"]["KEY"]))
            else:
                request = requests.post(CONFIGS['TWILIO']['SEND_URL'], json={"number":sys.argv[1], "text":message['body'][:1600]})
        except Exception as error:
            raise Exception(error)
        else:
            print(request.text)
        iter_count = iter_count +1

def reply_parser(message):
    '''
    # H1: This does't matter.... this defines the contents in the message
    but whether forwarded or not is included in the plain/text body
    if (H1) -> Custom parser must be built

    ----------------
    Content-Type: multipart/alternative; boundary="0000000000008912d505c593f421"

    --0000000000008912d505c593f421
    Content-Type: text/plain; charset="UTF-8"
    Content-Transfer-Encoding: quoted-printableo
    <reply to a multimedia image>
    ----------------


    ---------------------
    Content-Type: text/plain; charset="UTF-8"
    <single message not a reply>
    --------------------

    '''

    # get all sentences starting with '>'
    # TODO: keep checking for same pattern till the end to make sure it's truly the forwarded part
    s_message = re.split(r'\n> ', message)
    '''
    if len(s_message) > 1:
        print(s_message)
    
    '''
    # print(s_message[0])
    return s_message[0]

if __name__ == "__main__":
    import start_routines
    start_routines.sr_database_checks()
    messages=get_mails()
    print(messages)
    try:
        transmit_messages([messages[0]])
    except Exception as error:
        print(error)
