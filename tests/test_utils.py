import pytest

from utils.api_utils import create_service, AppType
from google.oauth2.credentials import Credentials


def test_create_service() -> None:
    creds = Credentials('something')
    for app in (AppType.GMAIL, AppType.CALENDAR):
        assert create_service(creds, app=app) is not None

    assert create_service(creds, app='test_app') is None
