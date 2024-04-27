import os
import nltk
from nltk.tokenize import sent_tokenize
import pickle

nltk.download('punkt')


def read_tokens_and_tags(file_path):
    data = []
    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            parts = line.strip().split()
            if len(parts) > 0:
                token, tag = parts[0], parts[-1]
                data.append((token, tag))
    return data


def process_documents(data):
    processed_documents = {}
    doc_id = 0
    processed_tokens = []
    for token, tag in data:
        processed_tokens.append((token, tag))
        if token == '.':
            processed_documents[doc_id] = processed_tokens
            doc_id += 1
            processed_tokens = []
    return processed_documents


def prepare_data_for_ner(data):
    prepared_sentences = []
    for doc_id, doc_tuples in data.items():
        reconstructed_doc = " ".join([word for word, tag in doc_tuples])
        sentences = sent_tokenize(reconstructed_doc)
        for sentence in sentences:
            sentence_tuples = [(word, tag) for word, tag in doc_tuples if word in sentence]
            prepared_sentences.append(sentence_tuples)
    return prepared_sentences


base_path = '/Users/danyapetrovich/Downloads/groningen_meaning_bank_modified'
file_path = os.path.join(base_path, 'gmb_subset_full.txt')

data = read_tokens_and_tags(file_path)
processed_data = process_documents(data)
prepared_data = prepare_data_for_ner(processed_data)

with open('prepared_data.pkl', 'wb') as file:
    pickle.dump(prepared_data, file)
