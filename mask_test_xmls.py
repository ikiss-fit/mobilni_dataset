import os
import sys
import argparse

from shutil import copy


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", required=True)
    parser.add_argument("-o", "--output", required=True)
    parser.add_argument("-f", "--files", help="Text file with list of xmls that should be masked. If not used, all input files are masked.", required=False, default=None)
    return parser.parse_args()


def load_files_list(path):
    files = []

    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            if len(line) > 0:
                files.append(line)

    return files


def mask_file(path):
    output = []

    with open(path, "r") as f:
        for line in f:
            line_stripped = line.strip()
            if not (line_stripped.startswith("<Unicode>") and line_stripped.endswith("</Unicode>")):
                output.append(line)

    return output


def save(data, path):
    with open(path, "w") as f:
        for line in data:
            f.write(line)


def copy_file(source, destination):
    copy(source, destination)


def mask(input_path, output_path, files_path):
    files = None
    counter = 0

    missing = ["18b048284ca2fc0516636dfcbe4d1001.jpg_rec.xml",
               "559983873c7f1171bb76725a523df490.jpg_rec.xml",
               "67467e8d0c3725ceb8a1d23b2bc97a85.jpg_rec.xml",
               "d09f861d6d5a1a0736e5594cba8099ee.jpg_rec.xml",
               "d82d6a7b62101c49f93442bca9a08eac.jpg_rec.xml",
               "e106367cd7dc510cf392f2808062ac3a.jpg_rec.xml"]

    if files_path is not None:
        files = load_files_list(files_path)

    input_files = [file for file in os.listdir(input_path) if file.endswith(".xml")]

    for input_file in input_files:
        if input_file in missing:
            print(input_file)

        if files_path is None or input_file[:-4] + ".jpg" in files:
            output = mask_file(os.path.join(input_path, input_file))
            save(output, os.path.join(output_path, input_file))
            counter += 1
            if input_file in missing:
                print("Masked")

            # print("Masked:", input_file)

        elif files_path is not None:
            copy_file(os.path.join(input_path, input_file), os.path.join(output_path, input_file))
            if input_file in missing:
                print("Copied")

    print("Totaly masked:", counter)


def main():
    args = parse_args()
    mask(args.input, args.output, args.files)

    return 0


if __name__ == "__main__":
    sys.exit(main())
