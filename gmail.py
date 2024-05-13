import base64
from email import message_from_bytes
from email.header import decode_header
from email.message import Message

from bs4 import BeautifulSoup

from utils.error_handling import http_error_catcher
from googleapiclient.discovery import Resource


def remove_empty_lines(text: str) -> str:
    lines = text.splitlines()
    non_empty_lines = [line for line in lines if line.strip()]
    text = "\n".join(non_empty_lines)
    return text.strip()


def decode_text(text: str) -> str:
    decoded_parts = decode_header(text)
    decoded_text = ""
    for part, encoding in decoded_parts:
        if isinstance(part, bytes):
            decoded_text += part.decode(encoding or "utf-8")
        else:
            decoded_text += part
    return decoded_text


def parse_raw_message(raw_message: str) -> tuple[Message, str]:
    decoded_bytes = base64.urlsafe_b64decode(raw_message)
    email_message = message_from_bytes(decoded_bytes)

    if email_message.is_multipart():
        for part in email_message.walk():
            if part.get_content_type() in ('text/plain', 'text/html'):
                body = part.get_payload(decode=True)
                if part.get_content_type() == 'text/html':
                    soup = BeautifulSoup(body, 'html.parser')
                    body = soup.get_text()
                else:
                    body = body.decode('utf-8')
                clean_body = remove_empty_lines(body)
                if clean_body:
                    return email_message, clean_body
    else:
        if email_message.get_content_type() in ('text/plain', 'text/html'):
            body = email_message.get_payload(decode=True)
            if email_message.get_content_type() == 'text/html':
                soup = BeautifulSoup(body, 'html.parser')
                body = soup.get_text()
            else:
                body = body.decode('utf-8')
            clean_body = remove_empty_lines(body)
            if clean_body:
                return email_message, clean_body
        else:
            return Message(), ''


def form_json_data(email: Message, full_body: str) -> dict[str, str]:
    data = {'body': full_body}
    sender = decode_text(email['From'])
    receiver = decode_text(email['To'])
    date = email['Date']
    subject = decode_text(email['Subject'])
    data.update({'sender': sender, 'receiver': receiver, 'send_date': date, 'subject': subject})
    return data


def get_letters(service: Resource, limit: int = 10, labels: str | list[str] = 'INBOX') -> dict[str, dict[str, str]]:
    letters = {}
    with http_error_catcher():
        message_results = service.users().messages().list(userId='me', labelIds=labels, maxResults=limit).execute()
        messages = message_results.get('messages', [])

        for i, message in enumerate(messages):
            message_info = service.users().messages().get(userId='me', id=message['id'], format='raw').execute()
            raw_message = message_info.get('raw')
            email, raw_message = parse_raw_message(raw_message)
            json_data = form_json_data(email, raw_message)
            letters[message['id']] = json_data
    return letters
