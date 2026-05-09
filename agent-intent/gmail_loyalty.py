print("gmail loyalty module loaded")
import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']


def gmail_login():
    creds = None

    # Load saved token if exists
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file(
            'token.json',
            SCOPES
        )

    # If not logged in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json',
                SCOPES
            )
            creds = flow.run_local_server(port=0)

        # Save token
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    return creds


if __name__ == "__main__":
    print("Logging into Gmail...")

    creds = gmail_login()

    print("✅ Gmail login successful!")

from googleapiclient.discovery import build

if __name__ == "__main__":
    print("Logging into Gmail...")

    creds = gmail_login()

    print("✅ Gmail login successful!")

    service = build('gmail', 'v1', credentials=creds)

    results = service.users().messages().list(
        userId='me',
        maxResults=5
    ).execute()

    messages = results.get('messages', [])

    print("\nRecent Emails:")

    for msg in messages:
        print(msg)