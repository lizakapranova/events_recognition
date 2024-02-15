import numpy as np
import torch
from torch.utils.data import Dataset, DataLoader
from transformers import BertTokenizerFast, BertForTokenClassification, Trainer, TrainingArguments
from sklearn.model_selection import train_test_split
import pickle
from seqeval.metrics import precision_score, recall_score, f1_score, classification_report
from transformers import EvalPrediction

from main import label_map_inverse, label_map, label_list


# Define a custom dataset class
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
    tokenized_inputs = {'input_ids': [], 'attention_mask': []}
    all_aligned_labels = []

    for sentence, label_seq in zip(sentences, labels):
        # Tokenize the sentence and create word_ids mapping
        inputs = tokenizer.encode_plus(sentence, add_special_tokens=True, max_length=max_length,
                                       padding='max_length', truncation=True, return_attention_mask=True,
                                       return_tensors="pt")
        word_ids = inputs.word_ids()

        # Create a new list for aligned labels
        aligned_label_ids = []

        previous_word_id = None
        label_index = 0

        for word_id in word_ids:
            if word_id is None:
                # Special tokens ([CLS], [SEP], padding) have no corresponding word and should be ignored in loss
                aligned_label_ids.append(-100)
            elif word_id != previous_word_id and label_index < len(label_seq):
                # Use label of the current word and increment label_index
                aligned_label_ids.append(label_map.get(label_seq[label_index], -100))
                label_index += 1
            else:
                # For subword tokens, set label to -100 (ignored in loss)
                aligned_label_ids.append(-100)

            previous_word_id = word_id

        if label_index != len(label_seq):
            print(f"Warning: Label alignment issue in sentence: {sentence}")

        # Append the results
        tokenized_inputs['input_ids'].append(inputs['input_ids'].squeeze())
        tokenized_inputs['attention_mask'].append(inputs['attention_mask'].squeeze())
        all_aligned_labels.append(torch.tensor(aligned_label_ids, dtype=torch.long))

    return tokenized_inputs, all_aligned_labels


def align_predictions(predictions, label_ids):
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
    preds_list, labels_list = align_predictions(p.predictions, p.label_ids)
    return {
        "precision": precision_score(labels_list, preds_list),
        "recall": recall_score(labels_list, preds_list),
        "f1": f1_score(labels_list, preds_list),
        "report": classification_report(labels_list, preds_list)
    }


with open('prepared_data.pkl', 'rb') as file:
    prepared_data = pickle.load(file)

# This should be your processed dataset


# Tokenization and label alignment
tokenizer = BertTokenizerFast.from_pretrained('bert-base-uncased')
sentences = [" ".join([word for word, label in sentence]) for sentence in prepared_data]
labels = [[label for word, label in sentence] for sentence in prepared_data]

train_sentences, val_sentences, train_labels, val_labels = train_test_split(sentences, labels, test_size=0.2)
val_sentences, test_sentences, val_labels, test_labels = train_test_split(val_sentences, val_labels, test_size=0.5)

# print("Number of sentences:", len(train_sentences))
# print("Number of label sequences:", len(train_labels))

train_encodings, train_labels = tokenize_and_align_labels(tokenizer, train_sentences, train_labels, label_map)
val_encodings, val_labels = tokenize_and_align_labels(tokenizer, val_sentences, val_labels, label_map)
test_encodings, test_labels = tokenize_and_align_labels(tokenizer, test_sentences, test_labels, label_map)

train_dataset = NERDataset(train_encodings, train_labels)
val_dataset = NERDataset(val_encodings, val_labels)
test_dataset = NERDataset(test_encodings, test_labels)

model = BertForTokenClassification.from_pretrained('bert-base-uncased', num_labels=len(label_list))

# Training arguments
training_args = TrainingArguments(
    output_dir='./results',
    num_train_epochs=3,
    per_device_train_batch_size=16,
    per_device_eval_batch_size=16,
    warmup_steps=500,
    weight_decay=0.01,
    logging_dir='./logs',
    evaluation_strategy="epoch"
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=val_dataset,
    compute_metrics=compute_metrics
)

# Evaluate the model (on test set)
eval_metrics = trainer.evaluate()

# Print metrics
print(eval_metrics)

model.save_pretrained('./results/my_model')
tokenizer.save_pretrained('./results/my_model')
