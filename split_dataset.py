import logging
import os
import sys
from time import gmtime, strftime
import decoding
import cv2

from line_transcription import LineTranscription


def parse_arguments():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--source', help='Path to source file (transcriptions).', required=True)
    parser.add_argument('-l', '--logs', help='Path to logs.', required=True)
    parser.add_argument('-c', '--crops', help='Path to crops.', required=True)
    parser.add_argument('-o', '--output', help='Path to output file.', required=True)
    parser.add_argument('--train', help='Path to file with train templates.')
    parser.add_argument('--valid', help='Path to file with valid templates.')
    parser.add_argument('--test', help='Path to file with test templates')
    args = parser.parse_args()
    return args


def load_lines(path):
    lines = []

    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            if len(line) > 0:
                transcription = LineTranscription.parse(line)
                lines.append(transcription)

    return lines


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


def get_used_templates(logs, crops_path):
    used_templates = set()

    images = []

    with open(crops_path, "r") as f:
        for line in f:
            images.append(line.split(".", maxsplit=1)[0])

    for image in images:
        if image in logs:
            used_templates.add(logs[image])
        else:
            print("Id", image, "not found in translation dictionary.")

    print("Used templates:", len(used_templates))

    return used_templates


def split_templates(logs, crops_path):
    used_templates = list(get_used_templates(logs, crops_path))

    templates_count = len(used_templates)

    split_index_1 = int(0.8 * templates_count)
    split_index_2 = int(0.1 * templates_count) + split_index_1

    train_templates = used_templates[:split_index_1]
    valid_templates = used_templates[split_index_1:split_index_2]
    test_templates = used_templates[split_index_2:]

    print("Train templates:", len(train_templates))
    print("Valid templates:", len(valid_templates))
    print("Test templates:", len(test_templates))

    return train_templates, valid_templates, test_templates


def decide_level(line, easy, medium, hard):
    if line.ler == 0.0:
        easy.append(line)
    elif line.ler < 0.2:
        medium.append(line)
    else:
        hard.append(line)


def split_lines(lines, logs, templates):
    train_easy, train_medium, train_hard = [], [], []
    valid_easy, valid_medium, valid_hard = [], [], []
    test_easy, test_medium, test_hard = [], [], []
    train_templates, valid_templates, test_templates = templates

    for line in lines:
        line_id, _ = line.filename.split(".", maxsplit=1)
        template = logs[line_id]

        if template in test_templates:
            decide_level(line, test_easy, test_medium, test_hard)
        elif template in valid_templates:
            decide_level(line, valid_easy, valid_medium, valid_hard)
        else:
            decide_level(line, train_easy, train_medium, train_hard)

    print(" {level:6} | {train:^6} | {valid:^6} | {test:^6} | {sum:^6}".format(level="level", train="train", valid="valid", test="test", sum="sum"))
    print("--------------------------------------------")
    print(" {level:6} | {train:6} | {valid:6} | {test:6} | {sum:6}".format(level="easy", train=len(train_easy), valid=len(valid_easy), test=len(test_easy), sum=len(train_easy)+len(valid_easy)+len(test_easy)))
    print("--------------------------------------------")
    print(" {level:6} | {train:6} | {valid:6} | {test:6} | {sum:6}".format(level="medium", train=len(train_medium), valid=len(valid_medium), test=len(test_medium), sum=len(train_medium)+len(valid_medium)+len(test_medium)))
    print("--------------------------------------------")
    print(" {level:6} | {train:6} | {valid:6} | {test:6} | {sum:6}".format(level="hard", train=len(train_hard), valid=len(valid_hard), test=len(test_hard), sum=len(train_hard)+len(valid_hard)+len(test_hard)))
    print("--------------------------------------------")
    print(" {level:6} | {train:6} | {valid:6} | {test:6} | {sum:6}".format(level="sum",
                                                                           train=len(train_easy) + len(train_medium) + len(train_hard),
                                                                           valid=len(valid_easy) + len(valid_medium) + len(valid_hard),
                                                                           test=len(test_easy) + len(test_medium) + len(test_hard),
                                                                           sum=len(lines)))

    return train_easy, train_medium, train_hard, valid_easy, valid_medium, valid_hard, test_easy, test_medium, test_hard


def save_lines(transcriptions, filepath):
    with open(filepath, "w") as f:
        for line in transcriptions:
            f.write(line.filename + " " + line.ground_truth + "\n")


def save(splitted_lines, path):
    train_easy, train_medium, train_hard, \
        valid_easy, valid_medium, valid_hard, \
        test_easy, test_medium, test_hard = splitted_lines

    save_lines(train_easy, os.path.join(path, "train.easy"))
    save_lines(train_medium, os.path.join(path, "train.medium"))
    save_lines(train_hard, os.path.join(path, "train.hard"))

    save_lines(valid_easy, os.path.join(path, "valid.easy"))
    save_lines(valid_medium, os.path.join(path, "valid.medium"))
    save_lines(valid_hard, os.path.join(path, "valid.hard"))

    save_lines(test_easy, os.path.join(path, "test.easy"))
    save_lines(test_medium, os.path.join(path, "test.medium"))
    save_lines(test_hard, os.path.join(path, "test.hard"))

    save_lines(train_easy + train_medium + train_hard, os.path.join(path, "lines.train"))
    save_lines(valid_easy + valid_medium + valid_hard, os.path.join(path, "lines.valid"))
    save_lines(test_easy + test_medium + test_hard, os.path.join(path, "lines.test"))


def save_templates(templates, path, name):
    with open(os.path.join(path, name), "w") as f:
        for template in templates:
            f.write(template + "\n")


def save_template_distribution(templates, path):
    train_templates, valid_templates, test_templates = templates

    save_templates(train_templates, path, name="templates.train")
    save_templates(valid_templates, path, name="templates.valid")
    save_templates(test_templates, path, name="templates.test")


def load_templates(path):
    templates = []

    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            if len(line) > 0:
                templates.append(line)

    return templates


def load_templates_distribution(train, valid, test):
    train_templates = load_templates(train)
    valid_templates = load_templates(valid)
    test_templates = load_templates(test)

    return train_templates, valid_templates, test_templates


def main():
    args = parse_arguments()

    lines = load_lines(args.source)
    logs = load_logs(args.logs)

    if args.train is None or args.valid is None or args.test is None:
        templates = split_templates(logs, args.crops)
        save_template_distribution(templates, args.output)
    else:
        templates = load_templates_distribution(args.train, args.valid, args.test)

    splitted_lines = split_lines(lines, logs, templates)

    save(splitted_lines, args.output)

    return 0


if __name__ == "__main__":
    sys.exit(main())