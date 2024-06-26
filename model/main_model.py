import re

from model.patterns import get_meeting_probability
from datetime import datetime, timedelta
import model.custom_spacy_model as custom_model
import dateparser


def parse_time(time_str):
    def parse_single_time(time_part):
        # Regex to match phrases like "five o'clock"
        match = re.match(r"(\w+) o'clock", time_part, re.IGNORECASE)
        if match:
            # Convert the matched word to a number
            word_to_number = {
                "one": "1:00",
                "two": "2:00",
                "three": "3:00",
                "four": "4:00",
                "five": "5:00",
                "six": "6:00",
                "seven": "7:00",
                "eight": "8:00",
                "nine": "9:00",
                "ten": "10:00",
                "eleven": "11:00",
                "twelve": "12:00"
            }
            normalized_time_part = word_to_number.get(match.group(1).lower(), time_part)
        else:
            normalized_time_part = time_part

        parsed_time = dateparser.parse(normalized_time_part)
        if parsed_time:
            return parsed_time.time()
        else:
            raise ValueError(f"Unable to parse time: {time_part}")

    if "-" in time_str:
        start_time_str, end_time_str = map(str.strip, time_str.split(" - "))
        start_time = parse_single_time(start_time_str)
        end_time = parse_single_time(end_time_str)
        return start_time, end_time
    else:
        time_obj = parse_single_time(time_str)
        return time_obj, None


def parse_date(date_str):
    if date_str.lower() in {"tomorrow", "tomorrow's", "tomorrow's day"}:
        return (datetime.now() + timedelta(days=1)).strftime("%d.%m.%Y")
    elif date_str.lower() == "in a day":
        return (datetime.now() + timedelta(days=2)).strftime("%d.%m.%Y")
    elif date_str.lower().startswith("in "):
        try:
            num_days = int(date_str.lower().split()[1])
            return (datetime.now() + timedelta(days=num_days)).strftime("%d.%m.%Y")
        except ValueError:
            raise ValueError("Invalid format for relative date")
    else:
        try:
            parsed_date = dateparser.parse(date_str, settings={'RELATIVE_BASE': datetime.now()})
            if parsed_date < datetime.now():
                raise ValueError("Date cannot be in the past")
            return parsed_date.strftime("%d.%m.%Y")
        except ValueError:
            raise ValueError("Invalid date format")


def extract_date_time_info(doc):
    date_entities = [ent for ent in doc.ents if ent.label_ == 'DATE']
    time_entities = [ent for ent in doc.ents if ent.label_ == 'TIME']
    date = [ent.text for ent in date_entities]
    time = [ent.text for ent in time_entities]
    time_parsed = parse_time(time[0])
    if len(date) != 0:
        date_parsed = parse_date(date[0])
    else:
        date_parsed = datetime.now().strftime("%d.%m.%Y")

    start_datetime = datetime.strptime(date_parsed, "%d.%m.%Y")
    start_datetime = start_datetime.replace(hour=time_parsed[0].hour, minute=time_parsed[0].minute, second=0)
    end_datetime = None
    if time_parsed[1] is not None:
        end_datetime = start_datetime.replace(hour=time_parsed[1].hour, minute=time_parsed[1].minute, second=0)
        end_datetime = end_datetime.isoformat()
    start_datetime = start_datetime.isoformat()

    return start_datetime, end_datetime


def _letter_prediction(data):
    text = data['body']
    model = custom_model.MySpaCyModel()

    doc = model.predict(text)

    answer = get_meeting_probability(data, doc)
    is_meeting = answer['is_meeting']
    if not is_meeting:
        return None
    # prob = answer['probability']

    # print(f"Letter with meeting: {is_meeting} (Probability: {prob})")

    loc_entities = [ent for ent in doc.ents if ent.label_ == 'LOC']
    loc = [ent.text for ent in loc_entities]

    description = ''
    if answer['reference'] is not None:
        description = f'''Reference: {answer['reference']}''' + '\n'
    elif len(loc) > 0:
        description = f'Location of meeting: {loc[0]}'

    start_datetime, end_datetime = extract_date_time_info(doc)

    event_type = model.classify_event_type()

    data = {
        'description': description,
        'event_type': event_type,
        'start': {
            'dateTime': start_datetime,
        },
        'end': {
            'dateTime': end_datetime,
        }
    }

    return data


def letters_prediction(letters: dict[str, dict[str, str]]):
    predictions = {}
    for email_id, letter in letters.items():
        prediction = _letter_prediction(letter)
        if prediction:
            predictions[email_id] = prediction
    return predictions
