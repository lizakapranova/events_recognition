from utils.api_utils import create_service, AppType
from google_calendar import add_event
from gmail import get_letters
from google.oauth2.credentials import Credentials
from model.main_model import letters_prediction

import os.path
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
SCOPES = ['https://www.googleapis.com/auth/calendar', 'https://www.googleapis.com/auth/gmail.readonly']


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


def script(creds: Credentials) -> str:
    # work with gmail
    gmail_service = create_service(creds, app=AppType.GMAIL)
    letters = get_letters(gmail_service)

    prediction_results = letters_prediction(letters)

    # work with calendar
    calendar_service = create_service(creds, app=AppType.CALENDAR)
    log = add_event(calendar_service, prediction_results)
    return log


if __name__ == '__main__':
    creds = get_credentials()
    script(creds)
