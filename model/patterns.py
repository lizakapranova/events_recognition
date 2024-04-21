def contains_date_time_entities(entities):
    has_date = any(label == 'I-DAT' or label == 'B-DAT' for _, label in entities)
    has_time = any(label == 'I-TIM' or label == 'B-TIM' for _, label in entities)
    return has_date or has_time


def contains_multiple_persons(entities):
    person_count = sum(1 for _, label in entities if label in ['I-PER', 'B-PER'])
    return person_count > 2


def check_sender_recipient_info(email_info: str, entities):
    keywords = ["manager", "coordinator", "secretary", "director", "HR", "head"]
    sender_title = email_info.split()[-1]
    recipient_title = email_info.split()[:-1]

    return any(keyword in sender_title for keyword in keywords) or \
        any(keyword in recipient_title for keyword in keywords)


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
    has_location = any(label == 'I-LOC' or label == 'B-LOC' for _, label in entities)
    has_tool = any(tool in text.lower() for tool in meeting_tools)
    return has_location or has_tool


def check_subject_and_body_for_meeting(subject, body):
    meeting_keywords = ["meeting", "appointment", "schedule", "call", "conference", "discussion", "webinar"]
    return any(keyword in subject.lower() for keyword in meeting_keywords) or any(
        keyword in body.lower() for keyword in meeting_keywords)


def get_meeting_probability(email_dict, entities):
    text = email_dict['body']

    probability_score = 0
    date_time_ent = 0.55  # Ключевое!
    sender_recipient_score = 0.02
    calendaring_phrases_score = 0.02
    conditional_statements_score = 0.01
    confirmatory_closures_score = 0.01
    meeting_tools_locations_score = 0.1
    persons = 0.2
    subject = 0.1

    if contains_date_time_entities(entities):
        probability_score += date_time_ent
        print('datetime')
    if check_sender_recipient_info(email_dict['sender'], entities):
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

    threshold = 0.6

    return probability_score > threshold, probability_score
