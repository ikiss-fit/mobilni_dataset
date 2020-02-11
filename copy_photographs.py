import os
import sys
import cv2
import argparse
import numpy as np
import datetime
from shutil import copy


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", required=True)
    parser.add_argument("-o", "--output", required=True)
    parser.add_argument("-t", "--translation-file", required=True)
    parser.add_argument("-r", "--rectified-photos-path", required=True)
    parser.add_argument("-p", "--original-photos-path", required=True)
    parser.add_argument("-l", "--logs-path", required=True)
    return parser.parse_args()


def load_translation(path):
    translation = {}

    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            id, photo_path = line.split()
            translation[id] = photo_path

    return translation


def parse_matrix_row(row):
    parts = row.split()
    return [float(part) for part in parts]


def fill_transformation_row(transformation, row, data):
    for index, value in enumerate(data):
        transformation[row][index] = value

    return transformation


def read_log(path):
    transformation_width = 3
    transformation_height = 3

    transformation = [[None for _ in range(transformation_width)] for _ in range(transformation_height)]

    with open(path, "r") as f:
        for index, line in enumerate(f):
            line = line.strip()

            if index == 3 and line.startswith("T  [[") and line.endswith("]"):
                transformation = fill_transformation_row(transformation, 0, parse_matrix_row(line[5:-1]))

            elif index == 4 and line.startswith("[") and line.endswith("]"):
                transformation = fill_transformation_row(transformation, 1, parse_matrix_row(line[1:-1]))

            elif index == 5 and line.startswith("[") and line.endswith("]]"):
                transformation = fill_transformation_row(transformation, 2, parse_matrix_row(line[1:-2]))

    return np.array(transformation)


def calculate_similarity(img1, img2, scale=0.25):
    i1 = cv2.resize(img1, (0, 0), fx=scale, fy=scale)
    i2 = cv2.resize(img2, (0, 0), fx=scale, fy=scale)

    return cv2.matchTemplate(i1, i2, cv2.cv2.TM_SQDIFF)[0][0]


def find_rotation(original_image, rectified_image, transformation):
    height, width, _ = original_image.shape
    rec_height, rec_width, _ = rectified_image.shape

    center = (width / 2, height / 2)
    scale = 1.0

    score0 = calculate_similarity(cv2.warpPerspective(original_image, transformation, (rec_width, rec_height)), rectified_image)

    rotated90 = cv2.rotate(original_image, cv2.cv2.ROTATE_90_CLOCKWISE)
    score90 = calculate_similarity(cv2.warpPerspective(rotated90, transformation, (rec_width, rec_height)), rectified_image)

    rotated180 = cv2.rotate(original_image, cv2.cv2.ROTATE_180)
    score180 = calculate_similarity(cv2.warpPerspective(rotated180, transformation, (rec_width, rec_height)), rectified_image)

    rotated270 = cv2.rotate(original_image, cv2.cv2.ROTATE_90_COUNTERCLOCKWISE)
    score270 = calculate_similarity(cv2.warpPerspective(rotated270, transformation, (rec_width, rec_height)), rectified_image)

    best = np.argmin([score0, score90, score180, score270])

    if best == 0:
        result = original_image
    elif best == 1:
        result = rotated90
    elif best == 2:
        result = rotated180
    else:
        result = rotated270

    return result


def process_directory(input_path, output_path, rectified_photos_path, original_photos_path, logs_path, translation):
    input_files = [file for file in os.listdir(input_path) if file.endswith(".xml")]

    total_files = len(input_files)

    for index, input_file in enumerate(input_files):
        print("\r{current}/{total} ({percentage:.2f} %)".format(current=index+1, total=total_files, percentage=100 * float(index+1) / total_files), end="")

        id = input_file.split(".")[0]
        original_photo_path = os.path.join(original_photos_path, translation[id])
        rectified_photo_path = os.path.join(rectified_photos_path, input_file[:-4] + ".jpg")

        transformation = read_log(logs_path + "/" + id + ".jpg.log")

        original_image = cv2.imread(original_photo_path)
        rectified_image = cv2.imread(rectified_photo_path)

        original_image = find_rotation(original_image, rectified_image, transformation)

        cv2.imwrite(output_path + "/" + id + ".jpg", original_image)

    print()


def main():
    args = parse_args()

    translation = load_translation(args.translation_file)

    process_directory(args.input, args.output, args.rectified_photos_path, args.original_photos_path, args.logs_path, translation)

    return 0


if __name__ == "__main__":
    sys.exit(main())
