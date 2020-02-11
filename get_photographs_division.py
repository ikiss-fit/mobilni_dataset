import os
import sys
import argparse

from shutil import copy


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", required=True)
    parser.add_argument("-o", "--output", required=True)
    parser.add_argument("-l", "--logs", required=True)
    parser.add_argument("-t", "--templates", required=True)
    return parser.parse_args()


def get_id_from_log(log_name, logs_folder):
    with open(os.path.join(logs_folder, log_name)) as f:
        for line in f:
            if line.startswith("TEMPLATE"):
                return line[line.rindex("/") + 1:line.rindex(".")]

    return None


def load_logs(path):
    log_names = [log_name for log_name in os.listdir(path) if log_name.endswith(".log")]

    translation = {}

    for log_name in log_names:
        page_id = get_id_from_log(log_name, path)

        if page_id is not None:
            translation[log_name[:log_name.index(".")]] = page_id

    return translation


def load_templates(path):
    files = []

    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            if len(line) > 0:
                files.append(line)

    return files


def save(data, path):
    with open(path, "w") as f:
        for line in data:
            f.write(line + "\n")


def get_photographs(input_path, logs, templates):
    photographs = []

    input_files = [file for file in os.listdir(input_path) if file.endswith(".jpg")]

    for input_file in input_files:
        id = input_file.split(".", maxsplit=1)[0]

        template = logs[id]
        if template in templates:
            photographs.append(input_file)

    return photographs


def main():
    args = parse_args()

    logs = load_logs(args.logs)
    templates = load_templates(args.templates)

    photographs = get_photographs(args.input, logs, templates)

    save(photographs, args.output)

    return 0


if __name__ == "__main__":
    sys.exit(main())
