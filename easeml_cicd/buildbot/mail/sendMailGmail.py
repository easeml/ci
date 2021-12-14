from __future__ import print_function

import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request


class EaseMailer:
    def __init__(self):
        self.scopes = 'https://www.googleapis.com/auth/gmail.send'
        # self.token_path = "./"
        self.token_path = "/home/ubuntu/ETH/easeml/keys/"
        self.secret_file = self.token_path + 'credentials.json'
        self.creds = None
        self.headless = False

    def get_update_credentials(self):
        # The file token.pickle stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if self.creds == None:
            if os.path.exists(self.token_path + 'token.pickle'):
                with open(self.token_path + 'token.pickle', 'rb') as token:
                    self.creds = pickle.load(token)
        # If there are no (valid) credentials available, let the user log in.
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.secret_file, self.scopes)
                if not self.headless:
                    self.creds = flow.run_local_server()
                else:
                    self.creds = flow.run_console()
            # Save the credentials for the next run
            with open(self.token_path + 'token.pickle', 'wb') as token:
                pickle.dump(self.creds, token)
        return

    def SendMessage(self, to, subject, msgHtml, sender="easemlbot@gmail.com"):
        self.get_update_credentials()
        service = build('gmail', 'v1', credentials=self.creds)
        message1 = self.CreateMessageHtml(sender, to, subject, msgHtml)
        result = self.SendMessageInternal(service, "me", message1)
        return result

    def SendMessageInternal(self, service, user_id, message):
        try:
            message = (service.users().messages().send(userId=user_id, body=message).execute())
            print('Message Id: %s' % message['id'])
            return message
        except errors.HttpError as error:
            print('An error occurred: %s' % error)
            return "Error"
        return "OK"

    def CreateMessageHtml(self, sender, to, subject, msgHtml):
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = sender
        msg['To'] = to
        # msg.attach(MIMEText(msgPlain, 'plain'))
        msg.attach(MIMEText(msgHtml, 'html'))
        return {'raw': base64.urlsafe_b64encode(msg.as_string().encode()).decode()}


if __name__ == '__main__':
    mail = EaseMailer()
    to = "leonel.aguilar.m@gmail.com"
    subject = "subject"
    msgHtml = "Hello world<br/>This is a mail sent by the ease.ml bot"
    mail.SendMessage(to, subject, msgHtml)
