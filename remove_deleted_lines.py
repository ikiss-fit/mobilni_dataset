import os
import sys
import argparse

from dataset import Dataset, Page


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--dataset", help="Path to XMLs.", required=False)
    parser.add_argument("-l", "--lines", help="Path to lines with transcriptions.", required=False)
    parser.add_argument("-o", "--output", help="Path to output.", required=False)
    args = parser.parse_args()
    return args


def load_lines(path):
    lines = {}

    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            if len(line) > 0:
                file, transcription = line.split(maxsplit=1)
                lines[file] = transcription

    return lines


def process_dataset(dataset, lines):
    new_dataset = Dataset(None)

    total_pages = len(dataset.pages)

    for index, page_id in enumerate(dataset.pages):
        print("{current}/{total} {percentage:.2f}".format(current=index, total=total_pages, percentage=100 * float(index)/total_pages))

        page = dataset.get_page(page_id)

        new_lines = []

        for index, line in enumerate(page.lines):
            filename = "{id}.jpg_rec_l{index:04d}.jpg".format(id=page_id, index=index)

            print("FILENAME ({filename}): {state}".format(filename=filename, state=filename in lines))

            if filename in lines and line.text == lines[filename]:
                new_lines.append(line)

        new_dataset.add_page(Page(page_id + ".jpg_rec", new_lines))

    return new_dataset


def main():
    args = parse_args()

    lines = load_lines(args.lines)

    dataset = Dataset(args.dataset, lazy=True)
    print(dataset)
    process_dataset(dataset, lines).save(args.output)

    return 0


if __name__ == "__main__":
    sys.exit(main())
