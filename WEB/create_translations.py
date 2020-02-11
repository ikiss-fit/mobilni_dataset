import os
import sys
import argparse


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--source', help='Path to source file (transcriptions).', required=True)
    parser.add_argument('-o', '--output', help='Path to output file.', required=True)
    args = parser.parse_args()
    return args


def load(path):
    lines = []
    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            if len(line) > 0:
                lines.append(line)

    return lines


def save(translations, path):
    with open(path, "w") as f:
        for key in translations:
            f.write("{key} {value}\n".format(key=key, value=translations[key]))


def create_translations(lines):
    translations = {}

    for index, line in enumerate(lines):
        file, _ = line.split(maxsplit=1)
        translations[file] = "{id}.jpg".format(id=index)

    return translations


def main():
    args = parse_arguments()

    save(create_translations(load(args.source)), args.output)

    return 0


if __name__ == "__main__":
    sys.exit(main())
