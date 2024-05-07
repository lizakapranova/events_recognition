from utils.api_utils import get_credentials, create_service, AppType
from google_calendar import add_event
from gmail import get_letters

def letters_predict(letters):
    return []



def main() -> None:
    creds = get_credentials()

    # work with gmail
    gmail_service = create_service(creds, app=AppType.GMAIL)
    letters = get_letters(gmail_service)

    prediction_results = letters_predict(letters)

    # work with calendar
    calendar_service = create_service(creds, app=AppType.CALENDAR)
    add_event(calendar_service, prediction_results)


if __name__ == '__main__':
    main()
