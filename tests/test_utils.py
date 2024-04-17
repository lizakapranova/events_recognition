import pytest

from utils.api_utils import create_service
from utils.errors import AppTypeError
from google.oauth2.credentials import Credentials


def test_create_service() -> None:
    creds = Credentials('something')
    try:
        create_service(creds, app='gmail')
    except AppTypeError:
        raise TypeError('This should not be a problem!')

    with pytest.raises(AppTypeError):
        create_service(creds, app='test_app')
