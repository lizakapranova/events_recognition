import json
from patterns import get_meeting_probability
import dateutil.parser
from datetime import datetime, timedelta

import spacy


def get_predictions(text):
    nlp = spacy.load('en_core_web_trf')
    doc = nlp(text)

    return doc


def parse_time(time_str):
    if "-" in time_str:
        start_time_str, end_time_str = time_str.split(" - ")
        start_time = dateutil.parser.parse(start_time_str)
        end_time = dateutil.parser.parse(end_time_str)
        return start_time.time(), end_time.time()
    else:
        time_obj = dateutil.parser.parse(time_str)
        return time_obj.time(), None


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
            parsed_date = dateutil.parser.parse(date_str, default=datetime.now())
            if parsed_date < datetime.now():
                raise ValueError("Date cannot be in the past")
            return parsed_date.strftime("%d.%m.%Y")
        except ValueError:
            raise ValueError("Invalid date format")


def main():
    f = open('../mail.json')
    data = json.load(f)
    text = data['body']

    doc = get_predictions(text)

    is_meeting, prob = get_meeting_probability(data, doc)

    print(f"Letter with meeting: {is_meeting} (Probability: {prob})")

    date_entities = [ent for ent in doc.ents if ent.label_ == 'DATE']
    time_entities = [ent for ent in doc.ents if ent.label_ == 'TIME']

    date = [ent.text for ent in date_entities]
    time = [ent.text for ent in time_entities]

    time_parsed = parse_time(time[0])
    if len(data) != 0:
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

    data = {
        'start': {
            'dateTime': start_datetime,
        },
        'end': {
            'dateTime': end_datetime,
        }
    }

    return data


if __name__ == '__main__':
    main()
