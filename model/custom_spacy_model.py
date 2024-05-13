import random

import spacy
import torch
from spacy.util import minibatch, compounding
from spacy.training import Example


class MySpaCyModel(torch.nn.Module):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # spacy.require_gpu()
        self.doc = None
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
        self.doc = self.nlp(text)
        return self.doc

    def classify_event_type(self):
        event_types = ["Meeting", "Call", "Reminder", "Unknown", "Webinar", "Conference"]
        event_type_scores = {}
        for event_type in event_types:
            score = self.doc.similarity(self.nlp(event_type))
            event_type_scores[event_type] = score

        highest_score = max(event_type_scores.values())
        chosen_event_type = [k for k, v in event_type_scores.items() if v == highest_score]

        if highest_score < 0.2:
            return "Unknown"

        if len(chosen_event_type) > 1:
            return random.choice(chosen_event_type)

        return chosen_event_type[0]
