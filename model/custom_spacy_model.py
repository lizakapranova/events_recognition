import random
import spacy
import torch
from spacy.util import minibatch, compounding
from spacy.training import Example
from torch.utils.tensorboard import SummaryWriter
from spacy.cli import download


class MySpaCyModel(torch.nn.Module):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.doc = None
        model_name = "en_core_web_lg"

        try:
            nlp = spacy.load(model_name)
        except OSError:
            download(model_name)
            nlp = spacy.load(model_name)
        self.writer = SummaryWriter()

    def fit(self, train_data):
        if torch.cuda.is_available():
            torch_device = torch.device('cuda')
            spacy.require_gpu()
            print("Using GPU for training")
        else:
            torch_device = torch.device('cpu')
            print("Using CPU for training")

        examples = []
        cnt = 0
        for doc in train_data:
            for sent in doc['sentences']:
                doc = self.nlp.make_doc(' '.join(sent['words']))
                entities = []
                for ent in doc.ents:
                    ent_label = sent['named_entities'][ent.start:ent.end]
                    entities.append((ent.start, ent.end, ent.label_, ent_label))
                example = Example.from_dict(doc, {'entities': entities})
                examples.append(example)
            cnt += 1

        optimizer = self.nlp.create_optimizer()

        print('Begin training')

        for itn in range(10):
            losses = {}
            batches = minibatch(examples, size=compounding(4.0, 32.0, 1.001))
            for batch in batches:
                self.nlp.update(batch, drop=0.2, sgd=optimizer, losses=losses)
            print(f"Iteration {itn} complete, loss: {losses}")

            # Log metrics to TensorBoard
            for key, value in losses.items():
                self.writer.add_scalar(f"Loss/{key}", value, itn)

        self.nlp.to_disk("/results/my_model")
        self.writer.close()

    def predict(self, text):
        self.doc = self.nlp(text)
        return self.doc

    def classify_event_type(self):
        if self.doc is None:
            raise ValueError("Document not set. Call predict() first.")

        event_types = ["Meeting", "Call", "Reminder", "Unknown", "Webinar", "Conference"]
        event_type_scores = {}

        print(f"Classifying event type for doc: {self.doc.text}")

        for event_type in event_types:
            event_type_doc = self.nlp(event_type)
            score = self.doc.similarity(event_type_doc)
            event_type_scores[event_type] = score
            print(f"Score for {event_type}: {score}")

        highest_score = max(event_type_scores.values())
        chosen_event_type = [k for k, v in event_type_scores.items() if v == highest_score]

        print(f"Event type scores: {event_type_scores}")
        print(f"Highest score: {highest_score}, Chosen event type(s): {chosen_event_type}")

        if highest_score < 0.2:
            print("Highest score below threshold, returning 'Unknown'")
            return "Unknown"

        if len(chosen_event_type) > 1:
            chosen = random.choice(chosen_event_type)
            print(f"Multiple event types with the same score, randomly chosen: {chosen}")
            return chosen

        print(f"Chosen event type: {chosen_event_type[0]}")
        return chosen_event_type[0]
