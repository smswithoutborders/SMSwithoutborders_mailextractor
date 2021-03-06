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
import time
from tqdm import tqdm
from email.parser import HeaderParser
from datastore import Datastore

CONFIGS = configparser.ConfigParser(interpolation=None)
PATH_CONFIG_FILE = os.path.join(os.path.dirname(__file__), '', 'config.ini')
CONFIGS.read(PATH_CONFIG_FILE)


imap_host = CONFIGS['IMAP']['HOST']
imap_user = CONFIGS['IMAP']['USER']
imap_pass = CONFIGS['IMAP']['PASSWORD']

imap = imaplib.IMAP4_SSL(imap_host)
imap.login(imap_user, imap_pass)
print("login successful")

imap.select('INBOX')

def check_ssl():
    return os.path.isfile( CONFIGS["SSL"]["KEY"] ) and os.path.isfile(CONFIGS["SSL"]["CRT"])

'''
- todo: remove copied message body - significantly reduces the sizes of some emails
'''

def mark_as_seen(e_id):
    imap.store(e_id, '+FLAGS', '\Seen')

def get_mails():
    typ, msgnums = imap.search(None, 'ALL', '(UNSEEN)')
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
    '''
    for i in tqdm(range(len(msgs)), "extracting..."):
        num = msgs[i]
    '''
    for num in msgs:
        mtyp, msg = imap.fetch(num, STANDARDS)
        data=msg[0][CONTENT_INDEX]
        msg = email.message_from_bytes(data)
        # print(msg.keys())
        # datastore = Datastore()
        ID = msg['Message-ID']
        From = msg['From']
        To = msg['To'].split(', ')
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
            for _to in To:
                message = {}
                message["from"] = From
                message["to"] = _to
                message["subject"] = Subject
                message["body"] = reply_parser(bytes.decode(Body))
                message["reply_to"] = reply_to
                message["cc"] = cc
                message["content_transfer_encoding"] = content_transfer_encoding
                message["encoding"] = encoding
                message["e_id"] = num

                messages.append(message)
                # mark_as_seen(num)
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


def parse_email(email):
    # name <email>
    return email.split(' ')[-1:][0].replace('<', '').replace('>', '')

def transmit_messages(messages):
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
        text=f"To: {message['to']}\nFrom: {message['from']}\nSubject: {message['subject']}\n\n{message['body']}"
        text=text[:1600]
        try:
            if check_ssl():
                response = requests.post(f"{CONFIGS['CLOUD_API']['DEV_URL']}/hash", json={"email":message['to']}, cert=(CONFIGS["SSL"]["CRT"], CONFIGS["SSL"]["KEY"]))
                response = response.json()
                if not 'phone_number' in response[0]:
                    raise Exception("no number acquired from router!")
                number = response['country_code'] + response['phone_number']
                request = requests.post(CONFIGS['TWILIO']['SEND_URL'], json={"number":number, "text":text}, cert=(CONFIGS["SSL"]["CRT"], CONFIGS["SSL"]["KEY"]))
            else:
                print(message)
                response = requests.post(f"{CONFIGS['CLOUD_API']['DEV_URL']}/hash", json={"email":parse_email(message['to'])})
                if not response.ok:
                    print(response.text)
                    continue
                    # raise Exception("no number acquired from router!")
                response = response.json()
                if len(response) < 1:
                    continue
                response = response[0]

                if not 'phone_number' in response:
                    raise Exception("no number acquired from router!")
                number = response['country_code'] + response['phone_number']
                # print(number)
                request = requests.post(CONFIGS['TWILIO']['SEND_URL'], json={"number":number, "text":text})
        except Exception as error:
            # print(error)
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
    # start_routines.sr_database_checks()
    print("daemon began")
    while True:
        # print("scanning for messages...")
        messages=get_mails()
        # print(messages)
        try:
            transmit_messages(messages)
        except Exception as error:
            print(error)

        time.sleep(int(CONFIGS['LOOPS']['SLEEP']))
    imap.close()
