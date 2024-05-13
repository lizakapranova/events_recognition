from dataclasses import dataclass
from typing import Any

import pytest

from google_calendar import create_event_structure
from datetime import datetime


def check_time_lapse(start: dict[str, str], end: dict[str, str]) -> bool:
    start_dt = datetime.fromisoformat(start['dateTime'])
    end_dt = datetime.fromisoformat(end['dateTime'])
    return end_dt.hour - start_dt.hour == 1 and start['timeZone'] == end['timeZone']


@dataclass
class StructureCase:
    name: str
    event_type: str
    other_fields: dict[str, Any]

    def __str__(self):
        return f"test_{self.name}"


TEST_CASES = [
    StructureCase(
        name='without_attendees',
        event_type='Meeting',
        other_fields={'title': 'Test Title',
                      'start': {
                          'dateTime': '2024-01-17T09:00:00-07:00'
                      },
                      'end': {
                          'dateTime': '2024-01-17T17:00:00-07:00'
                      },
                      'description': 'test_description'
                      }
    ),
    StructureCase(
        name='with_attendees',
        event_type='Meeting',
        other_fields={'title': 'Test Title',
                      'start': {
                          'dateTime': '2024-01-17T09:00:00-07:00'
                      },
                      'end': {
                          'dateTime': '2024-01-17T17:00:00-07:00'
                      },
                      'attendees': [
                          {'email': 'lpage@example.com'},
                          {'email': 'sbrin@example.com'},
                      ],
                      'description': 'test_description'
                      }
    ),
    StructureCase(
        name='missing_end',
        event_type='Meeting',
        other_fields={'title': 'Test Title',
                      'start': {
                          'dateTime': '2024-01-17T09:00:00-07:00'
                      },
                      'end': {
                          'dateTime': None
                      },
                      'description': 'test_description'}
    ),
]


@pytest.mark.parametrize("case", TEST_CASES, ids=str)
def test_create_event_structure(case: StructureCase) -> None:
    result = create_event_structure(case.event_type, **case.other_fields)
    assert 'start' in result and result['start'] == case.other_fields['start']
    if case.other_fields['end']['dateTime']:
        assert 'end' in result and result['end'] == case.other_fields['end']
    else:
        assert check_time_lapse(result['start'], result['end'])
    assert result['summary'].startswith(case.event_type)
    if 'attendees' in case.other_fields:
        for attendee in case.other_fields['attendees']:
            assert attendee in result['attendees']
    else:
        assert 'attendees' not in result
