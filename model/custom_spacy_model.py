import spacy
from spacy.util import minibatch, compounding
from spacy.training import Example
import torch


class MySpaCyModel(torch.nn.Module):
    def __init__(self):
        self.nlp = spacy.load("en_core_web_trf")

    def fit(self, train_data):
        examples = []
        cnt = 0
        for doc in train_data:
            if cnt == 3:
                break
            for sent in doc['sentences']:
                doc = self.nlp.make_doc(' '.join(sent['words']))
                entities = []
                for ent in doc.ents:
                    ent_label = sent['named_entities'][ent.start:ent.end]
                    entities.append((ent.start, ent.end, ent.label_, ent_label))
                example = Example.from_dict(doc, {'entities': entities})
                examples.append(example)
                print(cnt)
            cnt += 1

        optimizer = self.nlp.create_optimizer()

        print('Begin training')

        for itn in range(10):
            losses = {}
            batches = minibatch(examples, size=compounding(4.0, 32.0, 1.001))
            for batch in batches:
                self.nlp.update(batch, drop=0.2, sgd=optimizer, losses=losses)
            print(f"Iteration {itn} complete, loss: {losses}")
            # Calculate metrics on a validation set here

        self.nlp.to_disk("/results/my_model")

    def predict(self, text):
        doc = self.nlp(text)
        return doc
