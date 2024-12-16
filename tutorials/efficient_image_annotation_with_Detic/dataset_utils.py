import os

def save_labels(label_file, labels, boxes, probabilities):
    os.makedirs(os.path.dirname(label_file), exist_ok=True)
    with open(label_file, 'w') as f:
        for label, box, prob in zip(labels, boxes, probabilities):
            x_center, y_center, width, height = box
            f.write(f"{label} {x_center} {y_center} {width} {height} {prob}\n")