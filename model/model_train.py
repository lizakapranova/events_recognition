import torch
from datasets import load_dataset
from custom_spacy_model import MySpaCyModel


def train_model():
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    train_data = load_dataset("conll2012_ontonotesv5", "english_v4")['train']
    train_data = train_data.to(device)
    model = MySpaCyModel().to(device)
    model.fit(train_data)


if __name__ == '__main__':
    train_model()
