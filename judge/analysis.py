#
# For licensing see accompanying LICENSE file.
# Copyright (C) 2025 Apple Inc. All Rights Reserved.
#

import argparse
import json
import csv
import os
import re

def extract_labels_from_files(json_files):
    all_labels = set()
    for json_file in json_files:
        with open(json_file) as f:
            json_data = json.load(f)
            labels = {item['label'] for item in json_data}
            all_labels.update(labels)
    return sorted(all_labels)

def extract_predictions(json_data, all_labels, rev=False):
    label_predictions = {}
    pattern = re.compile(r'Dialog ([A-Za-z]) is better')
    for label in all_labels:
        prediction = 'M'  # Default prediction if label not found
        for item in json_data:
            if item['label'] == label:
                match = re.match(pattern, item['predict'])
                if match:
                    prediction = match.group(1)
                    if rev:
                        prediction = {"B":"A", "A":"B"}[prediction]
                break
        label_predictions[label] = prediction
    return label_predictions

def process_json_files(json_files):
    all_labels = extract_labels_from_files(json_files)
    combined_predictions = {}
    for json_file in json_files:
        with open(json_file) as f:
            json_data = json.load(f)
            label_predictions = extract_predictions(json_data, all_labels, rev = ("rev" in json_file))
            filename = os.path.basename(json_file)
            combined_predictions[filename] = label_predictions
    return combined_predictions

def write_combined_tsv(combined_predictions, input_folder):
    all_labels = sorted(combined_predictions[next(iter(combined_predictions))].keys())
    filenames = sorted(combined_predictions.keys())
    with open(os.path.join(input_folder, 'combined_predictions.tsv'), 'w', newline='') as tsvfile:
        writer = csv.writer(tsvfile, delimiter='\t')
        writer.writerow(['Label'] + filenames)
        for label in all_labels:
            row = [label]
            for filename in filenames:
                prediction = combined_predictions[filename].get(label, 'M')
                combined_predictions[filename][label] = prediction
                row.append(prediction)
            writer.writerow(row)

def transpose_predictions(combined_predictions):
    combined_predictions_transpose = {}
    for filename, label_predictions in combined_predictions.items():
        for label, prediction in label_predictions.items():
            if label not in combined_predictions_transpose:
                combined_predictions_transpose[label] = {}
            combined_predictions_transpose[label][filename] = prediction
    return combined_predictions_transpose


def find_consensus_predictions(combined_predictions):
    consensus_predictions = {}
    for label, predictions in combined_predictions.items():
        consensus_prediction = None
        for _, prediction in predictions.items():
            if consensus_prediction is None:
                consensus_prediction = prediction
            elif consensus_prediction != prediction:
                consensus_prediction = None
                break
        if consensus_prediction is not None:
            consensus_predictions[label] = consensus_prediction
    return consensus_predictions


def write_consensus_tsv(consensus_predictions, input_folder):
    prediction_counts = {'A': 0, 'B': 0, 'M': 0}  # Initializing counts for predictions A and B
    for prediction in consensus_predictions.values():
        prediction_counts[prediction] += 1
    
    with open(os.path.join(input_folder, 'consensus_predictions.tsv'), 'w', newline='') as tsvfile:
        writer = csv.writer(tsvfile, delimiter='\t')
        writer.writerow(['Prediction', 'Count'])
        for prediction, count in sorted(prediction_counts.items()):
            writer.writerow([prediction, count])
        writer.writerow(['Filename', 'Consensus Prediction'])
        for label, prediction in sorted(consensus_predictions.items(), key=lambda item: item[1]):
            writer.writerow([label, prediction])



def main():
    parser = argparse.ArgumentParser(description='Combine JSON files and create a single TSV')
    parser.add_argument('--input', required=True, help='Input folder containing JSON files')
    args = parser.parse_args()

    input_folder = args.input

    json_files = [os.path.join(input_folder, f) for f in os.listdir(input_folder) if f.endswith('.json')]

    combined_predictions = process_json_files(json_files)
    write_combined_tsv(combined_predictions, input_folder)

    consensus_predictions = find_consensus_predictions(transpose_predictions(combined_predictions))
    write_consensus_tsv(consensus_predictions, input_folder)

if __name__ == "__main__":
    main()

