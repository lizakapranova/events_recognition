import re


def contains_date_time_entities(entities):
    has_date = any(label == 'DATE' for _, label in entities)
    has_time = any(label == 'TIME' for _, label in entities)
    return has_date and has_time


def contains_multiple_persons(entities):
    person_count = sum(1 for _, label in entities if label == 'PERSON')
    return person_count > 2


def check_sender_recipient_info(email_info: str, doc):
    keywords = ["manager", "coordinator", "secretary", "director", "HR", "head"]
    sender_title = email_info.split()[-1]
    recipient_title = email_info.split()[:-1]

    # Find spans in the document that match the sender and recipient titles
    sender_spans = [span for span in doc.ents if span.text == sender_title]
    recipient_spans = [span for span in doc.ents if span.text == " ".join(recipient_title)]

    # Check if any of the spans match the keywords
    return any(keyword in span.text for keyword in keywords for span in sender_spans) or \
        any(keyword in span.text for keyword in keywords for span in recipient_spans)


def contains_video_conferencing_ref(text):
    video_conferencing_patterns = [
        r'\b(zoom)\b',
        r'\b(google meet)\b',
        r'\b(google hangouts)\b',
        r'\b(microsoft teams)\b',
        r'\b(teams)\b',  # in case "teams" is used without "Microsoft"
        r'\b(skype)\b',
        r'\b(webex)\b',
        r'\b(gotomeeting)\b',
        r'\b(bluejeans)\b'
    ]

    for pattern in video_conferencing_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)

    return None


def check_calendaring_phrases(text):
    calendaring_phrases = [
        "add to your calendar", "RSVP", "send a calendar invite", "save the date", "schedule", "arrange", "organize",
        "plan", "discuss", "call", "meet"
    ]
    return any(phrase in text.lower() for phrase in calendaring_phrases)


def check_conditional_statements(text):
    conditional_phrases = [
        "if you are available", "should you be able to", "if it fits your schedule"
    ]
    return any(phrase in text.lower() for phrase in conditional_phrases)


def check_confirmatory_closures(text):
    confirmatory_phrases = [
        "please confirm", "kindly confirm", "let me know", "confirm your attendance", "waiting for your reply"
    ]
    return any(phrase in text.lower() for phrase in confirmatory_phrases)


def contains_location_or_tool(entities, text):
    meeting_tools = ["zoom", "teams", "skype", "webex", "google meet"]
    has_location = any(label == 'LOC' for _, label in entities)
    has_tool = any(tool in text.lower() for tool in meeting_tools)
    return has_location or has_tool


def check_subject_and_body_for_meeting(subject, body):
    meeting_keywords = ["meeting", "appointment", "schedule", "call", "conference", "discussion", "webinar"]
    return any(keyword in subject.lower() for keyword in meeting_keywords) or any(
        keyword in body.lower() for keyword in meeting_keywords)


def get_meeting_probability(email_dict, doc):
    """
    Calculates the probability of a meeting occurrence based on the given email and doc object.

    Args:
        email_dict (dict): A dictionary containing the email information.
        doc (Doc): A spaCy Doc object containing the processed email text.

    Returns:
        tuple: A tuple containing a boolean indicating if the probability is above the threshold and the calculated probability score.
    """
    text = email_dict['body']

    probability_score = 0
    date_time_ent = 0.55  # Ключевое!
    sender_recipient_score = 0.02
    calendaring_phrases_score = 0.02
    conditional_statements_score = 0.03
    confirmatory_closures_score = 0.02
    meeting_tools_locations_score = 0.1
    persons = 0.13
    subject = 0.12
    ref = 0.05

    entities = [(ent.text, ent.label_) for ent in doc.ents]

    if contains_date_time_entities(entities):
        probability_score += date_time_ent
        print('datetime')
    if check_sender_recipient_info(email_dict['sender'], doc):
        probability_score += sender_recipient_score
        print('sender')
    if check_calendaring_phrases(text):
        probability_score += calendaring_phrases_score
        print('calendar')
    if check_conditional_statements(text):
        probability_score += conditional_statements_score
        print('conditional')
    if check_confirmatory_closures(text):
        probability_score += confirmatory_closures_score
        print('confirmatory')
    if contains_location_or_tool(entities, text):
        probability_score += meeting_tools_locations_score
        print('meeting tools')
    if contains_multiple_persons(entities):
        probability_score += persons
        print('persons')
    if check_subject_and_body_for_meeting(email_dict['subject'], text):
        probability_score += subject
        print('subject')
    if contains_video_conferencing_ref(text) is not None:
        probability_score += ref
        print('ref')

    threshold = 0.6

    data = {
        "is_meeting": probability_score > threshold,
        "probability": probability_score,
        "is_ref": contains_video_conferencing_ref(text),
        "persons": contains_multiple_persons(entities)
    }

    return data
