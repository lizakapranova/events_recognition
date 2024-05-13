from dataclasses import dataclass
from typing import Any

import pytest

from app.google_calendar import create_event_structure


@dataclass
class StructureCase:
    name: str
    event_type: str
    other_fields: dict[str, Any]

    def __str__(self):
        return f"test_{self.name}"


TEST_CASES_OK = [
    StructureCase(
        name='without_attendees',
        event_type='Meeting',
        other_fields={'title': 'Test Title',
                      'start': {
                          'dateTime': '2024-01-17T09:00:00-07:00',
                          'timeZone': 'America/Los_Angeles'
                      },
                      'end': {
                          'dateTime': '2024-01-17T17:00:00-07:00',
                          'timeZone': 'America/Los_Angeles'
                      }}
    ),
    StructureCase(
        name='with_attendees',
        event_type='Meeting',
        other_fields={'title': 'Test Title',
                      'start': {
                          'dateTime': '2024-01-17T09:00:00-07:00',
                          'timeZone': 'America/Los_Angeles'
                      },
                      'end': {
                          'dateTime': '2024-01-17T17:00:00-07:00',
                          'timeZone': 'America/Los_Angeles'
                      },
                      'attendees': [
                          {'email': 'lpage@example.com'},
                          {'email': 'sbrin@example.com'},
                      ]}
    )
]


@pytest.mark.parametrize("case", TEST_CASES_OK, ids=str)
def test_create_event_structure_ok(case: StructureCase) -> None:
    result = create_event_structure(case.event_type, **case.other_fields)
    assert 'start' in result and result['start'] == case.other_fields['start']
    assert 'end' in result and result['end'] == case.other_fields['end']
    assert result['summary'].startswith(case.event_type)
    if 'attendees' in case.other_fields:
        for attendee in case.other_fields['attendees']:
            assert attendee in result['attendees']
    else:
        assert 'attendees' not in result


TEST_CASES_WRONG = [
    StructureCase(
        name='missing_title',
        event_type='Meeting',
        other_fields={'start': {
            'dateTime': '2024-01-17T09:00:00-07:00',
            'timeZone': 'America/Los_Angeles'
        },
            'end': {
                'dateTime': '2024-01-17T17:00:00-07:00',
                'timeZone': 'America/Los_Angeles'
            }}
    ),
    StructureCase(
        name='missing_start',
        event_type='Meeting',
        other_fields={'title': 'Test Title',
                      'end': {
                          'dateTime': '2024-01-17T17:00:00-07:00',
                          'timeZone': 'America/Los_Angeles'
                      }}
    ),
    StructureCase(
        name='missing_end',
        event_type='Meeting',
        other_fields={'title': 'Test Title',
                      'start': {
                          'dateTime': '2024-01-17T09:00:00-07:00',
                          'timeZone': 'America/Los_Angeles'
                      }}
    ),
]


@pytest.mark.parametrize('case', TEST_CASES_WRONG, ids=str)
def test_create_event_structure_wrong(case: StructureCase) -> None:
    with pytest.raises(AssertionError):
        create_event_structure(case.event_type, **case.other_fields)
