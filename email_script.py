#!/usr/bin/env python
#
# Very simple Python script to dump all emails in an IMAP folder to files.  
# This code is released into the public domain.
#
# RKI Nov 2013
# Top Secret/PRISM Documents
# print(get_subject(data))

import sys
import imaplib , email
import getpass
import os
import time

IMAP_SERVER = "mail.web4u.cz"
EMAIL_ACCOUNT = ''
EMAIL_FOLDER = " INBOX.TEST_PY"
OUTPUT_DIRECTORY = 'log_download'
ATTACHMENT_DIR = 'prilohy'
PASSWORD = ''

def is_new_log_msg(msg,possition_end_msg):
    if msg.count(b'.') == 2:
        poz = msg.find(b'.')
        #print(str(possition_end_msg)+"_"+str(poz))
        if msg[poz+1] == 32 or msg[poz+1] == 33 or msg[poz+1] == 64 or msg[poz+1] == 65 or msg[poz+1] == 66 or msg[poz+1] == 128 or msg[poz+1] == 129:
            if (possition_end_msg - poz) > 12:  #vyradí staré správy napr. 1111.AA1908028
                return True
    return False

def get_body(msg):
    if msg.is_multipart():
        return get_body(msg.get_payload(0))
    else:
        return msg.get_payload(decode=True) #decode=true znamená ze dokóduje mime format

def get_subject(data):
    subject = None
    for res_part in data:
        if isinstance(res_part, tuple):
            msg = email.message_from_bytes(res_part[1])
            subject = msg['subject']
        return subject

def switch_only_log_message_room(num,num_tele,raw_msg):
    #sem pridávam len miestnosti ktoré posielajú logovacie správy cize sú po update
    print_message = "Parse message "+ str(num)
    directory = os.path.dirname(os.path.abspath(__file__))
    byte_body = get_body(raw_msg)
    possition_start_msg = byte_body.find(b'Sm:') + 5
    possition_end_msg =  byte_body.find(b'Em.')

    if is_new_log_msg(byte_body,possition_end_msg) == False:   #ak to nie je logová správe preskočí ju.
        return

    #povolenie hladať logovacie správy iba v miestnostiach v ktorých prichádzajú
    if num_tele == '002' or num_tele == '003':
        directory = directory + "\\log_download\\tele-" + str(num_tele)
        if not os.path.exists(directory):
            os.makedirs(directory)
        position = byte_body.find(b'2019')
        filePath = directory.encode() + b'\\' + byte_body[position:position+8] + b'.bin'
        log_file = open(filePath,'a+b')
        log_file.write(byte_body[possition_start_msg:possition_end_msg])
        log_file.close()
        print(print_message + "--->tele-" + str(num_tele))
            
        """elif num_tele == '003':
        directory = directory + "\\log_download\\tele-03"
        if not os.path.exists(directory):
            os.makedirs(directory)
        position = byte_body.find(b'2019')
        filePath = directory.encode() + b'\\' + byte_body[position:position+8] + b'.bin'
        log_file = open(filePath,'a+b')
        log_file.write(byte_body[possition_start_msg:possition_end_msg])
        log_file.close()
        print(print_message + "--->tele-003")"""

def get_attachments(msg):
    for part in msg.walk():
        if part.get_content_maintype()=='multipart':
            continue
        if part.get('Content-Disposition') is None:
            continue        
        name = part.get_filename()
        fileName = "igm_" + name[5:len(name)]
        if bool(fileName):
            filePath = os.path.join(ATTACHMENT_DIR, fileName)
            with open(filePath,'wb') as ff:
                ff.write(part.get_payload(decode=True))
                #print(str(part.get_payload(decode=True))+"_!_!")

def process_mailbox(M):
    """
    Dump all emails in the folder to files in output directory.
    """

    rv, data = M.search(None, "ALL")
    if rv != 'OK':
        print ("No messages found!")
        return

    #-------parse all exist email in email folder-------
    last_msg = data[0].split()[-1]
    for num in data[0].split():
        rv, data = M.fetch(num, '(RFC822)')
        
        if rv != 'OK':
            print ("ERROR getting message"+ str(num))
            return

        #__parsing__
        subject_num_tele = get_subject(data)
        raw = email.message_from_bytes(data[0][1])
        switch_only_log_message_room(num,subject_num_tele,raw)

    #-------wait and check new emails--------
    while True:
        rv, data_a = M.search(None, "ALL")#M.select(EMAIL_FOLDER, readonly=True)

        if data_a[0].split()[-1] == last_msg:
            print(data_a[0].split()[-1])
            time.sleep(2)
        else:
            print("__New_msg__")
            last_msg = data_a[0].split()[-1]
            result, data = M.fetch(last_msg, '(RFC822)')
            #__parsing__
            subject_num_tele = get_subject(data)
            raw = email.message_from_bytes(data[0][1])
            switch_only_log_message_room(last_msg,subject_num_tele,raw)
            time.sleep(2)

def main():
    M = imaplib.IMAP4_SSL(IMAP_SERVER)
    M.login(EMAIL_ACCOUNT, PASSWORD)
    rv, data = M.select(EMAIL_FOLDER, readonly=True)
    if rv == 'OK':
        print ("Processing mailbox: "+ EMAIL_FOLDER)
        process_mailbox(M)
        M.close()
    else:
        print ("ERROR: Unable to open mailbox "+ rv)
    M.logout()

if __name__ == "__main__":
    print("RUNING")
    main()
