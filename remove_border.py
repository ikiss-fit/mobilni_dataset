import sys
import cv2
from os import listdir
from os.path import isfile, join, abspath, basename


BORDER = 0.1


def parse_arguments():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--source-folder', help='Source folder.', required=True)
    parser.add_argument('-d', '--destination-folder', help='Destination folder.', required=True)
    args = parser.parse_args()
    return args


def get_file_names_from_folder(folder_path):
    return [abspath(join(folder_path, f)) for f in listdir(folder_path) if isfile(join(folder_path, f))]


def process_file(file_name):
    image = cv2.imread(file_name)
    height, width, channels = image.shape

    border_size = int(BORDER * width)

    new_image = image[border_size:-border_size, border_size:-border_size]
    return new_image


def save_file(image, folder, file_name):
    cv2.imwrite(join(folder, file_name), image)


def main():
    args = parse_arguments()

    file_names = get_file_names_from_folder(args.source_folder)

    for file_name in file_names:
        if file_name.endswith(".png"):
            print(basename(file_name))
            new_image = process_file(file_name)
            save_file(new_image, args.destination_folder, basename(file_name))

    return 0


if __name__ == "__main__":
    sys.exit(main())
