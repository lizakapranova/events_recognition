import os
import nltk
from nltk.tokenize import sent_tokenize
import pickle

nltk.download('punkt')


def read_tokens_and_tags(token_file, tag_file):
    # Read the token file
    with open(token_file, 'r', encoding='utf-8') as file:
        tokens_data = file.readlines()

    # Read the NER tag file
    with open(tag_file, 'r', encoding='utf-8') as file:
        tags_data = file.readlines()

    return tokens_data, tags_data


def process_tags(tag_line):
    parts = tag_line.strip().split('\t')
    if len(parts) > 1:
        return parts[-1]  # Returning the last part as the NER tag
    return 'O'


def process_documents(data):
    processed_documents = {}

    # Iterate over each document in the dictionary
    for doc_id, doc_data in data.items():
        processed_tokens = []
        # Process each token and tag pair
        for token_line, tag_line in zip(doc_data['tokens'], doc_data['tags']):
            # Split the token line and extract necessary parts
            token_parts = token_line.strip().split()
            token = token_parts[-1]  # The actual word is the last part of the line

            # Split the tag line and extract necessary parts
            tag_parts = tag_line.split('\t')
            ner_tag = tag_parts[-1][:-1] if len(tag_parts) == 5 else 'O'  # The NER tag is the last part of the line

            # Append the processed token and its corresponding NER tag
            processed_tokens.append((token, ner_tag))

        # Store the processed tokens for the current document
        processed_documents[doc_id] = processed_tokens

    return processed_documents


def prepare_data_for_ner(data):
    """
    Prepares the data for NER training.

    Args:
    data (dict): A dictionary with document IDs as keys and lists of (word, tag) tuples as values.

    Returns:
    list: A list of sentences, each sentence is a list of (word, tag) tuples.
    """
    prepared_sentences = []

    for doc_id, doc_tuples in data.items():
        # Reconstruct the document text from tokens for sentence tokenization
        reconstructed_doc = " ".join([word for word, tag in doc_tuples])

        # Split the document into sentences
        sentences = sent_tokenize(reconstructed_doc)

        # Initialize an index to keep track of the position in the list of tuples
        index = 0

        for sentence in sentences:
            sentence_length = len(sentence.split())
            sentence_tuples = doc_tuples[index: index + sentence_length]
            prepared_sentences.append(sentence_tuples)
            index += sentence_length

    return prepared_sentences


base_path = '/Users/petrovichdan/Downloads/gmb-1.0.0/data'

# Initialize a dictionary to hold tokens and tags for each document
data = {}

# Iterate over the 'pXX' directories
for p_dir_name in os.listdir(base_path):
    p_dir_path = os.path.join(base_path, p_dir_name)
    if os.path.isdir(p_dir_path):
        # Iterate over the 'dXXXX' directories within each 'pXX' directory
        for d_dir_name in os.listdir(p_dir_path):
            d_dir_path = os.path.join(p_dir_path, d_dir_name)
            if os.path.isdir(d_dir_path):
                # Define file paths for the tokens and tags
                token_file_path = os.path.join(d_dir_path, 'en.tok.off')
                tag_file_path = os.path.join(d_dir_path, 'en.tags')

                # Read files if they exist
                if os.path.exists(token_file_path) and os.path.exists(tag_file_path):
                    tokens_data, tags_data = read_tokens_and_tags(token_file_path, tag_file_path)
                    # Store in the dictionary
                    data[d_dir_name] = {
                        'tokens': tokens_data,
                        'tags': tags_data
                    }

processed_data = process_documents(data)

# print(data[next(iter(data))])
#
# print(processed_data[next(iter(processed_data))])

prepared_data = prepare_data_for_ner(processed_data)


with open('prepared_data.pkl', 'wb') as file:
    pickle.dump(prepared_data, file)
