from googleapiclient.discovery import Resource

from utils.error_handling import http_error_catcher


def create_event_structure(event_type: str, title: str, start: dict[str, str], end: dict[str, str],
                           attendees: list[dict[str, str]] | None = None) -> dict[str, str]:
    if attendees:
        summary = f'{event_type} with {", ".join([attendee["email"] for attendee in attendees])}: {title}'
        event = {
            'summary': summary,
            'start': start,
            'end': end,
            'attendees': attendees
        }
    else:
        summary = f'{event_type}: {title}'
        event = {
            'summary': summary,
            'start': start,
            'end': end
        }
    return event


def add_event(service: Resource) -> None:
    with http_error_catcher():
        calendars_result = service.calendarList().list().execute()
        calendars = calendars_result.get('items', [])
        primary_calendar_id = next((calendar['id'] for calendar in calendars if calendar.get('primary')), None)
        event = create_event_structure(event_type='meeting', title='Google I/O 2015', start={
            'dateTime': '2024-01-17T09:00:00-07:00',
            'timeZone': 'America/Los_Angeles'
        }, end={
            'dateTime': '2024-01-17T17:00:00-07:00',
            'timeZone': 'America/Los_Angeles'
        }, attendees=[
            {'email': 'lpage@example.com'},
            {'email': 'sbrin@example.com'},
        ])

        event = service.events().insert(calendarId=primary_calendar_id, body=event).execute()
        print(f"Event created: {event.get('htmlLink')}")

# EXAMPLE OF EVENT:
# event = {
#     'summary': 'Google I/O 2015',
#     'location': '800 Howard St., San Francisco, CA 94103',
#     'description': 'A chance to hear more about Google\'s developer products.',
#     'start': {
#         'dateTime': '2024-01-17T09:00:00-07:00',
#         'timeZone': 'America/Los_Angeles',
#     },
#     'end': {
#         'dateTime': '2024-01-17T17:00:00-07:00',
#         'timeZone': 'America/Los_Angeles',
#     },
#     'recurrence': [
#         'RRULE:FREQ=DAILY;COUNT=2'
#     ],
#     'attendees': [
#         {'email': 'lpage@example.com'},
#         {'email': 'sbrin@example.com'},
#     ],
#     'reminders': {
#         'useDefault': False,
#         'overrides': [
#             {'method': 'email', 'minutes': 24 * 60},
#             {'method': 'popup', 'minutes': 10},
#         ],
#     },
# }
