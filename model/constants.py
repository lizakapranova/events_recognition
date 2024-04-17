label_list = ['O', 'I-ORG', 'I-PER', 'I-LOC', 'I-MISC', 'B-ORG', 'B-PER', 'B-LOC', 'B-MISC', 'I-DAT', 'I-TIM']
label_map = {label: i for i, label in enumerate(label_list)}

label_map_inverse = {i: label for label, i in label_map.items()}
