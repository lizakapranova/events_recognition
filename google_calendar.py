from googleapiclient.discovery import Resource

from utils.error_handling import http_error_catcher


def create_event_structure(**fields):
    for field in ('start', 'end'):
        assert field in fields, f'You should set a {field} of event'
    event = {
        'summary': f"Meeting: {fields['title']}",
        'start': fields['start'],
        'end': fields['end'],
        'description': fields['description']
    }
    if 'attendees' in fields:
        event.update({'attendees': fields['attendees']})
    return event


def add_event(service: Resource, events: list[dict[str, str]]) -> str:
    log = 'Logging of Google Calendar:\n'
    with http_error_catcher():
        calendars_result = service.calendarList().list().execute()
        calendars = calendars_result.get('items', [])
        primary_calendar_id = next((calendar['id'] for calendar in calendars if calendar.get('primary')), None)
        # This is an example for now, I need to change this
        # events.append({'type': 'meeting', 'title': 'Google I/O 2015', 'start': {
        #     'dateTime': '2024-01-17T09:00:00-07:00',
        #     'timeZone': 'America/Los_Angeles'
        # }, 'end': {
        #     'dateTime': '2024-01-17T17:00:00-07:00',
        #     'timeZone': 'America/Los_Angeles'
        # }, 'attendees': [
        #     {'email': 'lpage@example.com'},
        #     {'email': 'sbrin@example.com'},
        # ]})
        for event_info in events:
            event = create_event_structure(**event_info)
            event = service.events().insert(calendarId=primary_calendar_id, body=event).execute()
            log += f"Event created: {event.get('htmlLink')}\n"
    return log

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
