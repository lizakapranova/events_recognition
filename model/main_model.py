from transformers import BertTokenizer, BertForTokenClassification
import torch
from patterns import get_meeting_probability
import json

from constants import label_map_inverse


def predict_entities(text, tokenizer, model, label_map):
    """
    Tokenizes the input text using the provided tokenizer, makes predictions using the model,
    and converts the predicted token IDs to tokens and their corresponding labels based on the label_map.

    Parameters:
    - text: The input text to predict entities from.
    - tokenizer: The tokenizer used to tokenize the input text.
    - model: The model used to make predictions.
    - label_map: A mapping of label IDs to their corresponding labels.

    Returns:
    - entities: A list of tuples where each tuple contains a token and its predicted label.
    """
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True, max_length=512)

    with torch.no_grad():
        outputs = model(**inputs)
    predictions = torch.argmax(outputs.logits, dim=-1)

    input_ids = inputs["input_ids"].squeeze()
    pred_labels = predictions.squeeze()

    entities = []
    for token_id, label_id in zip(input_ids.tolist(), pred_labels.tolist()):
        token = tokenizer.convert_ids_to_tokens(token_id)
        label = label_map.get(label_id, "Unknown")  # Handle unknown labels
        entities.append((token, label))

    return entities


def main():
    """
    Function to execute the main logic of the program.
    """
    tokenizer = BertTokenizer.from_pretrained('../results/my_model')
    model = BertForTokenClassification.from_pretrained('../results/my_model')

    f = open('./mail.json')

    data = json.load(f)

    entities_with_meeting = predict_entities(data['body'], tokenizer, model,
                                             label_map_inverse)  # это не ок, что все разбивается на слова (или даже меньше), из-за этого плохо предсказывает
    # entities_without_meeting = predict_entities(second_letter, tokenizer, model)
    print(entities_with_meeting)

    is_meeting, prob = get_meeting_probability(data, entities_with_meeting)

    print(f"Letter with meeting: {is_meeting} (Probability: {prob})")


if __name__ == '__main__':
    main()
