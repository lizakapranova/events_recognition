import re

import numpy as np
import torch
from transformers import BertTokenizerFast, BertForTokenClassification, Trainer, TrainingArguments
from sklearn.model_selection import train_test_split
import pickle
from seqeval.metrics import precision_score, recall_score, f1_score, classification_report
from transformers import EvalPrediction
from constants import label_list, label_map, label_map_inverse
from torch.utils.data import Dataset


class NERDataset(Dataset):
    def __init__(self, encodings, labels):
        self.encodings = encodings
        self.labels = labels

    def __getitem__(self, idx):
        item = {key: torch.tensor(val[idx]) for key, val in self.encodings.items()}
        item['labels'] = torch.tensor(self.labels[idx])
        return item

    def __len__(self):
        return len(self.labels)


def tokenize_and_align_labels(tokenizer, sentences, labels, label_map, max_length=128):
    """Tokenize sentences and align labels with tokens."""
    tokenized_inputs = {'input_ids': [], 'attention_mask': []}
    all_aligned_labels = []

    time_regex = re.compile(r'(\d{1,2}(:\d{2}){1,2}(am|pm))')

    for sentence, label_seq in zip(sentences, labels):
        # Replace time expressions with a special token
        sentence = time_regex.sub('[TIME]', sentence)

        # Tokenize the sentence and create word_ids mapping
        inputs = tokenizer.encode_plus(sentence, add_special_tokens=True, max_length=max_length,
                                       padding='max_length', truncation=True, return_attention_mask=True,
                                       return_tensors="pt")
        word_ids = inputs.word_ids()

        # Create a new list for aligned labels
        aligned_label_ids = []

        previous_word_id = None
        label_index = 0

        # Keep track of the start and end indices of time expressions
        time_start = -1
        time_end = -1

        for word_index, word_id in enumerate(word_ids):
            if word_id is None:
                # Special tokens ([CLS], [SEP], padding) have no corresponding word and should be ignored in loss
                aligned_label_ids.append(-100)
            elif word_id != previous_word_id and label_index < len(label_seq):
                # Use label of the current word and increment label_index
                if time_start != -1 and time_end != -1:
                    # If the current word is part of a time expression, use the label for the entire expression
                    if time_start <= word_index <= time_end:
                        aligned_label_ids.append(label_map.get('I-DAT', -100))
                    else:
                        aligned_label_ids.append(label_map.get(label_seq[label_index], -100))
                        label_index += 1
                else:
                    aligned_label_ids.append(label_map.get(label_seq[label_index], -100))
                    label_index += 1

                # Check if the current word is a time expression
                if word_ids[word_index] == tokenizer.convert_tokens_to_ids('[TIME]'):
                    time_start = word_index
                    time_end = word_index + 1

                    # Find the end index of the time expression
                    while word_ids[time_end] is not None and time_end < len(word_ids):
                        time_end += 1
            else:
                # For subword tokens, set label to -100 (ignored in loss)
                aligned_label_ids.append(-100)

                # Update the end index of the time expression
                if time_start != -1 and time_end != -1:
                    time_end = word_index + 1

            previous_word_id = word_id

        if label_index != len(label_seq):
            print(f"Warning: Label alignment issue in sentence: {sentence}")

        # Append the results
        tokenized_inputs['input_ids'].append(inputs['input_ids'].squeeze())
        tokenized_inputs['attention_mask'].append(inputs['attention_mask'].squeeze())
        all_aligned_labels.append(torch.tensor(aligned_label_ids, dtype=torch.long))

    return tokenized_inputs, all_aligned_labels


def align_predictions(predictions, label_ids):
    """Align predictions with actual labels."""
    # Convert logits to predicted label indices
    preds = np.argmax(predictions, axis=2)

    batch_size, seq_len = preds.shape
    labels_list, preds_list = [], []

    for batch_index in range(batch_size):
        labels, preds_labels = [], []
        for seq_index in range(seq_len):
            # Check if the index is within the range of label_ids for the current sentence
            if seq_index < len(label_ids[batch_index]):
                label_id = label_ids[batch_index][seq_index]
                pred_label_id = preds[batch_index][seq_index]

                # Only consider non-ignored labels (-100)
                if label_id != -100:
                    labels.append(label_map_inverse[label_id])
                    preds_labels.append(label_map_inverse[pred_label_id])

        labels_list.append(labels)
        preds_list.append(preds_labels)

    return preds_list, labels_list


def compute_metrics(p: EvalPrediction):
    """Compute metrics for evaluation."""
    preds_list, labels_list = align_predictions(p.predictions, p.label_ids)
    return {
        "precision": precision_score(labels_list, preds_list),
        "recall": recall_score(labels_list, preds_list),
        "f1": f1_score(labels_list, preds_list),
        "report": classification_report(labels_list, preds_list)
    }


def load_data(file_path):
    """Load data from pickle file."""
    with open(file_path, 'rb') as file:
        return pickle.load(file)


def split_data(sentences, labels):
    """Split data into train, validation, and test sets."""
    train_sentences, val_sentences, train_labels, val_labels = train_test_split(sentences, labels, test_size=0.2)
    val_sentences, test_sentences, val_labels, test_labels = train_test_split(val_sentences, val_labels, test_size=0.5)
    return train_sentences, val_sentences, test_sentences, train_labels, val_labels, test_labels


def main():
    """
    This function is the main entry point of the program.
    It loads prepared data, initializes a tokenizer, preprocesses the data, splits it into train/validation/test sets,
    tokenizes the data, creates datasets, initializes a model, trains the model, evaluates the model on the test set,
    prints the evaluation metrics, and saves the model and tokenizer.

    Parameters:
    None

    Returns:
    None
    """
    # Load data
    prepared_data = load_data('/Users/petrovichdan/PycharmProjects/CourseMailModel/prepared_data.pkl')

    # Initialize tokenizer
    tokenizer = BertTokenizerFast.from_pretrained('bert-base-uncased')

    # Preprocess data
    sentences = [" ".join([word for word, label in sentence]) for sentence in prepared_data]
    labels = [[label for word, label in sentence] for sentence in prepared_data]
    print(sentences)

    # Split data
    train_sentences, val_sentences, test_sentences, train_labels, val_labels, test_labels = split_data(sentences,
                                                                                                       labels)

    # Tokenize data
    train_encodings, train_labels = tokenize_and_align_labels(tokenizer, train_sentences, train_labels, label_map)
    print(train_encodings)
    val_encodings, val_labels = tokenize_and_align_labels(tokenizer, val_sentences, val_labels, label_map)
    test_encodings, test_labels = tokenize_and_align_labels(tokenizer, test_sentences, test_labels, label_map)

    # Create datasets
    train_dataset = NERDataset(train_encodings, train_labels)
    val_dataset = NERDataset(val_encodings, val_labels)
    test_dataset = NERDataset(test_encodings, test_labels)

    # Initialize model
    model = BertForTokenClassification.from_pretrained('bert-base-uncased', num_labels=len(label_list))

    # Unfreeze more layers for fine-tuning
    for name, param in model.named_parameters():
        if 'bert' in name and any(layer in name for layer in ['layer._0', 'layer._1', 'layer._2', 'layer._3']):
            param.requires_grad = True

    # Define training arguments with learning rate scheduler and early stopping
    training_args = TrainingArguments(
        output_dir='./results',
        num_train_epochs=10,  # increased number of epochs
        per_device_train_batch_size=32,  # increased batch size
        per_device_eval_batch_size=32,  # increased batch size
        warmup_steps=500,
        weight_decay=0.01,
        logging_dir='./logs',
        evaluation_strategy="steps",  # change evaluation strategy to "steps"
        save_strategy="steps",  # set save strategy to "steps"
        save_steps=1000,  # save the model every 1000 steps
        learning_rate=2e-5,
        lr_scheduler_type="linear",  # added learning rate scheduler
        load_best_model_at_end=True,  # added early stopping
        metric_for_best_model='f1',  # added early stopping
        greater_is_better=True,  # added early stopping
    )

    # Initialize trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        compute_metrics=compute_metrics
    )

    # Train the model
    trainer.train()

    # Evaluate the model (on test set)
    eval_metrics = trainer.evaluate(test_dataset)

    # Print metrics
    print(eval_metrics)

    # Save model and tokenizer
    model.save_pretrained('./results/my_model')
    tokenizer.save_pretrained('./results/my_model')


if __name__ == "__main__":
    main()
