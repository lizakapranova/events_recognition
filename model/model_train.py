import spacy
from spacy.util import minibatch, compounding
from datasets import load_dataset
from spacy.training import Example
from model import MySpaCyModel


def train_model():
    train_data = load_dataset("conll2012_ontonotesv5", "english_v4")['train']

    model = MySpaCyModel()
    model.fit(train_data)


if __name__ == '__main__':
    train_model()
