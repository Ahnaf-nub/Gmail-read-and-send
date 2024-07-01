import os.path
import time
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from bs4 import BeautifulSoup

# If modifying these scopes, delete the file token.json.
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.modify"
]

def get_message_body(msg):
    if 'parts' in msg['payload']:
        for part in msg['payload']['parts']:
            if part['mimeType'] == 'text/plain':
                return base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
            elif part['mimeType'] == 'text/html':
                html = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                soup = BeautifulSoup(html, 'html.parser')
                return soup.get_text()
    else:
        return base64.urlsafe_b64decode(msg['payload']['body']['data']).decode('utf-8')

def create_reply_message(original_message, reply_text):
    message_id = original_message['id']
    thread_id = original_message['threadId']
    headers = original_message['payload']['headers']
    for header in headers:
        if header['name'] == 'From':
            sender = header['value']
        if header['name'] == 'Subject':
            subject = header['value']

    reply_subject = "Re: " + subject if not subject.startswith("Re: ") else subject
    reply_message = MIMEText(reply_text)
    reply_message['to'] = sender
    reply_message['from'] = "me"
    reply_message['subject'] = reply_subject
    reply_message['threadId'] = thread_id

    raw_message = base64.urlsafe_b64encode(reply_message.as_bytes()).decode('utf-8')
    return {'raw': raw_message, 'threadId': thread_id}

def main():
    """Shows basic usage of the Gmail API.
    Lists the user's Gmail labels.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    try:
        # Call the Gmail API
        service = build("gmail", "v1", credentials=creds)
        results = service.users().messages().list(userId='me', labelIds=['INBOX'], q="is:unread").execute()
        messages = results.get('messages', [])
        if not messages:
            print("Check again later!")
        else:
            msg_count = 0
            for message in messages:
                msg = service.users().messages().get(userId='me', id=message['id']).execute()
                msg_count += 1
            print("You have " + str(msg_count) + " unread messages.")
            new_msg_choice = input("Would you like to see your messages?").lower()

            ''' if new_msg_choice in ('yes', 'y'):
                for message in messages:
                    msg = service.users().messages().get(userId='me', id=message['id']).execute()
                    email_data = msg['payload']['headers']
                    for values in email_data:
                        name = values['name']
                        if name == 'From':
                            from_name = values["value"]
                            print("You have a new message from: " + from_name)
                            print("Subject: " + next(j["value"] for j in email_data if j["name"] == "Subject"))
                            print("Message body:")
                            print(get_message_body(msg))
                            print("="*50) '''

                # Reply to the first unread message with "Ok"
            if messages:
                first_message = service.users().messages().get(userId='me', id=messages[0]['id']).execute()
                reply_message = create_reply_message(first_message, "Ok")
                send_message = service.users().messages().send(userId='me', body=reply_message).execute()
                print("Replied to the first unread message with 'Ok'.")

    except HttpError as error:
        # TODO - Handle errors from gmail API.
        print(f"An error occurred: {error}")

if __name__ == "__main__":
    main()
