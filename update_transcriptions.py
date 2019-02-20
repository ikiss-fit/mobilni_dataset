import sys
import argparse
import decoding


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--dataset-transcriptions", required=True)
    parser.add_argument("-t", "--test-transcriptions", required=True)
    parser.add_argument("-o", "--output-file", required=True)
    args = parser.parse_args()
    return args


def load_transcriptions(path):
    transcriptions = {}

    with open(path, "r") as f:
        for line in f:
            if len(line.strip()) > 0:
                filename, transcription = line.strip().split(maxsplit=1)
                transcriptions[filename] = transcription

    return transcriptions


def search_in_dataset(dataset, filename, transcription):
    result = None

    base_filename = filename.rsplit("_", maxsplit=1)[0]
    possible_files = [f for f in dataset if f.startswith(base_filename)]

    best_match_distance = None
    transcription_chars = [c for c in transcription]

    for possible_file in possible_files:
        distance = decoding.levenshtein_distance([c for c in dataset[possible_file]], transcription_chars)

        if best_match_distance is None or best_match_distance > distance:
            best_match_distance = distance
            result = possible_file

    return result


def update(dataset_transcriptions, test_transcriptions):
    updated_transcriptions = []

    for filename in test_transcriptions:
        dataset_filename = search_in_dataset(dataset_transcriptions, filename, test_transcriptions[filename])

        if dataset_filename is not None:
            updated_transcriptions.append("{filename} {transcription}\n".format(filename=dataset_filename, transcription=test_transcriptions[filename]))

    return updated_transcriptions

def main():
    args = parse_args()

    dataset_transcriptions = load_transcriptions(args.dataset_transcriptions)
    test_transcriptions = load_transcriptions(args.test_transcriptions)

    updated_transcriptions = update(dataset_transcriptions, test_transcriptions)

    with open(args.output_file, "w") as f:
        for transcription in updated_transcriptions:
            f.write(transcription)

    return 0


if __name__ == "__main__":
    sys.exit(main())