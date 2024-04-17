from contextlib import contextmanager

from googleapiclient.errors import HttpError


@contextmanager
def http_error_catcher() -> None:
    try:
        yield
    except HttpError as error:
        print(f"An error occurred: {error}")
