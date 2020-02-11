import os
import sys
import argparse


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('-l', '--lines', help='Path to source file (transcriptions).', required=True)
    parser.add_argument('-t', '--translations', help='Path to translation file.', required=True)
    parser.add_argument('-o', '--output', help='Path to output file.', required=True)
    parser.add_argument('-r', '--reverse', help='Flag, whether the translation should be done in reverse way.', required=False, action="store_true", default=False)
    args = parser.parse_args()
    return args


def load_lines(path):
    lines = []
    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            if len(line) > 0:
                lines.append(line)

    return lines


def load_translations(path, reverse=False):
    translations = {}
    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            if len(line) > 0:
                first, second = line.split(maxsplit=1)
                if not reverse:
                    translations[first] = second
                else:
                    translations[second] = first

    return translations


def save(lines, path):
    with open(path, "w") as f:
        for line in lines:
            f.write("{line}\n".format(line=line))


def translate(lines, translations):
    translated = []

    for line in lines:
        file, transcription = line.split(maxsplit=1)
        if file in translations:
            translated.append("{file} {transcription}".format(file=translations[file], transcription=transcription))
        else:
            print("Could not find '{file}' in the translation.".format(file=file))

    return translated


def main():
    args = parse_arguments()

    save(translate(load_lines(args.lines), load_translations(args.translations, args.reverse)), args.output)

    return 0


if __name__ == "__main__":
    sys.exit(main())
