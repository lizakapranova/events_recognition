from utils.api_utils import get_credentials, create_service
from google_calendar import add_event
from gmail import get_letters


def main() -> None:
    creds = get_credentials()

    # work with gmail
    gmail_service = create_service(creds, app='gmail')
    get_letters(gmail_service)

    # work with calendar
    calendar_service = create_service(creds, app='calendar')
    add_event(calendar_service)


if __name__ == '__main__':
    main()
