import spacy
from spacy.util import minibatch, compounding
from datasets import load_dataset
from spacy.training import Example

# Load the spaCy model
nlp = spacy.load('en_core_web_trf')

# Load the training data
train_data = load_dataset("conll2012_ontonotesv5", "english_v4")['train']

examples = []
cnt = 0
for doc in train_data:
    if cnt == 3:
        break
    for sent in doc['sentences']:
        doc = nlp.make_doc(' '.join(sent['words']))
        entities = []
        for ent in doc.ents:
            ent_label = sent['named_entities'][ent.start:ent.end]
            entities.append((ent.start, ent.end, ent.label_, ent_label))
        example = Example.from_dict(doc, {'entities': entities})
        examples.append(example)
        print(cnt)
    cnt += 1

optimizer = nlp.create_optimizer()

print('Begin training')

for itn in range(10):
    losses = {}
    batches = minibatch(examples, size=compounding(4.0, 32.0, 1.001))
    for batch in batches:
        print(len(batch))
        print('-' * 10)
        nlp.update(batch, drop=0.2, sgd=optimizer, losses=losses)
    print(f"Iteration {itn} complete, loss: {losses}")

nlp.to_disk("/results/my_model")
