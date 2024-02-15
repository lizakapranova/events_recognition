from transformers import BertTokenizer, BertForTokenClassification
import torch
from patterns import get_meeting_probability
import json

tokenizer = BertTokenizer.from_pretrained('./results/my_model')
model = BertForTokenClassification.from_pretrained('./results/my_model')

f = open('mail.json')

data = json.load(f)

label_list = ['O', 'I-ORG', 'I-PER', 'I-LOC', 'I-MISC', 'B-ORG', 'B-PER', 'B-LOC', 'B-MISC', 'I-DAT', 'I-TIM']
label_map = {label: i for i, label in enumerate(label_list)}

label_map_inverse = {i: label for label, i in label_map.items()}


def predict_entities(text, tokenizer, model, label_map):
    # Tokenize the input text
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True, max_length=512)

    # Get model predictions
    with torch.no_grad():
        outputs = model(**inputs)
    predictions = torch.argmax(outputs.logits, dim=-1)

    # Flatten the tensors for iteration
    input_ids = inputs["input_ids"].squeeze()
    pred_labels = predictions.squeeze()

    # Convert predicted token IDs to tokens and their labels
    entities = []
    for token_id, label_id in zip(input_ids.tolist(), pred_labels.tolist()):
        token = tokenizer.convert_ids_to_tokens(token_id)
        label = label_map.get(label_id, "Unknown")  # Handle unknown labels
        entities.append((token, label))

    return entities


entities_with_meeting = predict_entities(data['body'], tokenizer, model, label_map_inverse)
# entities_without_meeting = predict_entities(second_letter, tokenizer, model)

is_meeting_with, prob_with = get_meeting_probability(data, entities_with_meeting)
# is_meeting_without, prob_without = get_meeting_probability({}, second_letter)

print(f"Letter with meeting: {is_meeting_with} (Probability: {prob_with})")
