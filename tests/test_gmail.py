import base64
from dataclasses import dataclass
from email.header import Header
from email.message import EmailMessage
from enum import Enum
from typing import Callable
from datetime import datetime

import pytest

from app.gmail import decode_text, remove_empty_lines, parse_raw_message, form_json_data
from utils.errors import ContentError


@dataclass
class TextFormatCase:
    name: str
    func: Callable[[str], str]
    text: str | bytes
    expected: str

    def __str__(self):
        return f"test_{self.name}"


FORMAT_CASES = [
    TextFormatCase(
        name='decode_text_0',
        func=decode_text,
        text='=?utf-8?Q?Hello, world!?=',
        expected='Hello, world!'
    ),
    TextFormatCase(
        name='decode_text_1',
        func=decode_text,
        text='=?utf-8?Q?=D0=9F=D1=80=D0=B8=D0=B2=D0=B5=D1=82, =D0=BC=D0=B8=D1=80!?=',
        expected='Привет, мир!'
    ),
    TextFormatCase(
        name='decode_text_2',
        func=decode_text,
        text='',
        expected=''
    ),
    TextFormatCase(
        name='decode_text_3',
        func=decode_text,
        text=Header('Hello, world!', 'utf-8').encode(),
        expected='Hello, world!'
    ),
    TextFormatCase(
        name='remove_empty_lines_0',
        func=remove_empty_lines,
        text='',
        expected=''
    ),
    TextFormatCase(
        name='remove_empty_lines_1',
        func=remove_empty_lines,
        text='\n\r\r\n',
        expected=''
    ),
    TextFormatCase(
        name='remove_empty_lines_2',
        func=remove_empty_lines,
        text='\nHello, world!\n',
        expected='Hello, world!'
    ),
]


@pytest.mark.parametrize("case", FORMAT_CASES, ids=str)
def test_text_formatting(case: TextFormatCase) -> None:
    assert case.func(case.text) == case.expected


class EmailStructure(Enum):
    PLAIN_ONLY = 'plain_only'
    PLAIN_HTML = 'plain_html'
    HTML_ONLY = 'html_only'
    HTML_PLAIN = 'html_plain'
    WRONG = 'wrong'


def make_raw_message(structure: EmailStructure) -> str:
    email_msg = EmailMessage()
    email_msg['From'] = 'sender@example.com'
    email_msg['To'] = 'receiver@example.com'
    email_msg['Subject'] = 'Test Subject'
    match structure:
        case EmailStructure.PLAIN_ONLY:
            email_msg.set_content('This is a test message.')
        case EmailStructure.PLAIN_HTML:
            email_msg.set_content("This is the plain text part of the message.")
            email_msg.add_alternative("""\
                <html>
                  <body>
                    <p>This is the HTML part of the message.</p>
                  </body>
                </html>
                """, subtype='html')
        case EmailStructure.HTML_ONLY:
            email_msg.add_alternative("""\
                <html>
                  <body>
                    <p>This is a test message.</p>
                  </body>
                </html>
                """, subtype='html')
        case EmailStructure.HTML_PLAIN:
            email_msg.add_alternative("""\
                <html>
                  <body>
                    <p>This is the HTML part of the message.</p>
                  </body>
                </html>
                """, subtype='html')
            email_msg.add_alternative("This is the plain text part of the message.")
        case EmailStructure.WRONG:
            email_msg.set_content("""\
                <?xml version="1.0"?>
                <data>
                    <item>Hello, world!</item>
                </data>
                """, subtype='xml')

    raw_email_bytes = email_msg.as_bytes()
    return base64.urlsafe_b64encode(raw_email_bytes).decode('utf-8')


@dataclass
class RawMessageCase:
    name: str
    email: str
    original_body: str

    def __str__(self):
        return f"test_{self.name}"


RAW_MESSAGE_CASES = [
    RawMessageCase(
        name=EmailStructure.PLAIN_ONLY.value,
        email=make_raw_message(EmailStructure.PLAIN_ONLY),
        original_body='This is a test message.'
    ),
    RawMessageCase(
        name=EmailStructure.HTML_ONLY.value,
        email=make_raw_message(EmailStructure.HTML_ONLY),
        original_body='This is a test message.'
    ),
    RawMessageCase(
        name=EmailStructure.PLAIN_HTML.value,
        email=make_raw_message(EmailStructure.PLAIN_HTML),
        original_body='This is the plain text part of the message.'
    ),
    RawMessageCase(
        name=EmailStructure.HTML_PLAIN.value,
        email=make_raw_message(EmailStructure.HTML_PLAIN),
        original_body='This is the HTML part of the message.'
    ),
]

RAW_MESSAGE_CASES_WRONG = [
    RawMessageCase(
        name=EmailStructure.WRONG.value,
        email=make_raw_message(EmailStructure.WRONG),
        original_body='Hello, world!'
    )
]


@pytest.mark.parametrize("case", RAW_MESSAGE_CASES, ids=str)
def test_parse_raw_message_ok(case: RawMessageCase) -> None:
    _, parsed_message = parse_raw_message(case.email)
    assert parsed_message == case.original_body


@pytest.mark.parametrize("case", RAW_MESSAGE_CASES_WRONG, ids=str)
def test_parse_raw_message_wrong(case) -> None:
    with pytest.raises(ContentError):
        parse_raw_message(case.email)


@pytest.fixture(scope='function')
def email_message() -> EmailMessage:
    email_msg = EmailMessage()
    email_msg['From'] = 'sender@example.com'
    email_msg['To'] = 'receiver@example.com'
    email_msg['Subject'] = 'Test Subject'
    email_msg['Date'] = datetime(2024, 1, 17, 12)
    email_msg.set_content('This is a test message.')
    return email_msg


def test_forming_json_dict(email_message: EmailMessage) -> None:
    json_data = form_json_data(email_message, 'This is a test message.', 'test_id')
    assert 'email_id' in json_data and json_data['email_id'] == 'test_id'
    assert 'sender' in json_data and json_data['sender'] == 'sender@example.com'
    assert 'receiver' in json_data and json_data['receiver'] == 'receiver@example.com'
    assert 'subject' in json_data and json_data['subject'] == 'Test Subject'
    assert 'send_date' in json_data and json_data['send_date'] == 'Wed, 17 Jan 2024 12:00:00 -0000'
    assert 'body' in json_data and json_data['body'] == 'This is a test message.'

