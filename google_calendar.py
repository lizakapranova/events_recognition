from datetime import datetime, timedelta
from typing import Any
import pytz
from googleapiclient.discovery import Resource

from utils.error_handling import http_error_catcher


def create_event_structure(event_type='Meeting', **fields):
    start_dt = datetime.fromisoformat(fields['start']['dateTime'])
    time_zone = 'Europe/Moscow'
    fields['start'].update({'timeZone': time_zone})
    if fields['end']['dateTime'] is None:
        end_dt = start_dt + timedelta(hours=1)
        fields['end']['dateTime'] = end_dt.isoformat()
    fields['end'].update({'timeZone': time_zone})

    # event_type = 'Meeting' if event_type == 'Unknown' else event_type

    event = {
        'summary': f"{event_type}: {fields['title']}",
        'start': fields['start'],
        'end': fields['end'],
        'description': fields['description']
    }

    if 'attendees' in fields:
        event.update({'attendees': fields['attendees']})
    return event


def add_event(service: Resource, events: dict[str, dict[str, str | Any]], emails: dict[str, dict[str, str]]) -> str:
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
