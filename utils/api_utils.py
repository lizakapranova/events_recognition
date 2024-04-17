import os.path
from enum import Enum

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build, Resource

from .errors import AppTypeError

SCOPES = ['https://www.googleapis.com/auth/calendar', 'https://www.googleapis.com/auth/gmail.readonly']


class AppType(Enum):
    GMAIL = 'gmail'
    CALENDAR = 'calendar'


def get_credentials() -> Credentials:
    creds = None
    if os.path.exists('auth/token.json'):
        creds = Credentials.from_authorized_user_file('auth/token.json', SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('auth/credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)

        with open('auth/token.json', 'w') as token_file:
            token_file.write(creds.to_json())
    return creds


def create_service(credentials: Credentials, *, app: str) -> Resource:
    match app:
        case AppType.GMAIL.value:
            return build('gmail', 'v1', credentials=credentials)
        case AppType.CALENDAR.value:
            return build("calendar", "v3", credentials=credentials)
        case _:
            raise AppTypeError
