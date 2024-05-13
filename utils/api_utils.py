from enum import Enum

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build, Resource

from utils.errors import AppTypeError
from typing import Any


class AppType(Enum):
    GMAIL = 'gmail'
    CALENDAR = 'calendar'


def create_service(credentials: Credentials, *, app: AppType) -> Resource:
    match app:
        case AppType.GMAIL:
            return build('gmail', 'v1', credentials=credentials)
        case AppType.CALENDAR:
            return build("calendar", "v3", credentials=credentials)
        case _:
            raise AppTypeError


def credentials_to_dict(credentials: Credentials) -> dict[str, Any]:
    return {
        "token": credentials.token,
        "refresh_token": credentials.refresh_token,
        "token_uri": credentials.token_uri,
        "client_id": credentials.client_id,
        "client_secret": credentials.client_secret,
        "scopes": credentials.scopes,
    }