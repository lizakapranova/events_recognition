from utils.api_utils import create_service, AppType
from google_calendar import add_event
from gmail import get_letters
from google.oauth2.credentials import Credentials

def letters_predict(letters):
    return []


def script(creds: Credentials) -> None:

    # work with gmail
    gmail_service = create_service(creds, app=AppType.GMAIL)
    letters = get_letters(gmail_service)

    prediction_results = letters_predict(letters)

    # work with calendar
    calendar_service = create_service(creds, app=AppType.CALENDAR)
    log = add_event(calendar_service, prediction_results)
    return log
