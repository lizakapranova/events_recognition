from googleapiclient.discovery import Resource

from utils.error_handling import http_error_catcher
from typing import Any


def create_event_structure(**fields):
    fields['start'].update({'timeZone': 'Europe/Moscow'})
    fields['end'].update({'timeZone': 'Europe/Moscow'})
    event = {
        'summary': f"Meeting: {fields['title']}",
        'start': fields['start'],
        'end': fields['end'],
        'description': fields['description']
    }
    if 'attendees' in fields:
        event.update({'attendees': fields['attendees']})
    return event


def add_event(service: Resource, events: dict[str, dict[str, str | Any]], emails:dict[str, dict[str, str]]) -> str:
    log = 'Logging of Google Calendar:\n'
    with http_error_catcher():
        calendars_result = service.calendarList().list().execute()
        calendars = calendars_result.get('items', [])
        primary_calendar_id = next((calendar['id'] for calendar in calendars if calendar.get('primary')), None)
        for email_id, event_info in events.items():
            event_info['title'] = emails[email_id]['subject']
            event = create_event_structure(**event_info)
            event = service.events().insert(calendarId=primary_calendar_id, body=event).execute()
            log += f"Event created: {event.get('htmlLink')}\n"
    return log
