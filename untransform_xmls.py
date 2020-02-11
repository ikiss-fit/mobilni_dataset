import os
import sys
import cv2
import math
import argparse
import numpy as np
from dataset import Dataset, Point, Line, Page, Baseline, BoundingBox


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", required=True)
    parser.add_argument("-o", "--output", required=True)
    parser.add_argument("-l", "--logs", required=True)
    return parser.parse_args()


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


def transform_point(point, transformation):
    np_point = np.array([[float(point.x), float(point.y)]])
    np_new_point = cv2.perspectiveTransform(np_point[None, :, :], transformation)
    new_point = Point(int(round(np_new_point[0][0][0])), int(round(np_new_point[0][0][1])))

    return new_point


def process_dataset(dataset, log_path):
    new_dataset = Dataset()

    total_pages = len(dataset.pages)

    for index, page_id in enumerate(dataset.pages):
        print("\r{current}/{total} ({percentage:.2f} %)".format(current=index+1, total=total_pages, percentage=100 * float(index+1) / total_pages), end="")

        transformation = read_log(os.path.join(log_path, page_id.split(".")[0] + ".jpg.log"))

        try:
            inversion = np.linalg.inv(transformation)
        except:
            print("\nPage ID: {id}".format(id=page_id))
            print("Transformation matrix: {matrix}".format(matrix=transformation))
            continue

        page = dataset.get_page(page_id)

        lines = []

        if page.lines is not None:
            for line in page.lines:
                new_bb_start = transform_point(line.bounding_box.start, inversion)
                new_bb_end = transform_point(line.bounding_box.end, inversion)

                new_bb_inner_points = []

                if line.bounding_box.inner_points is not None:
                    for point in line.bounding_box.inner_points:
                        new_bb_inner_points.append(transform_point(point, inversion))

                new_baseline_start = transform_point(line.baseline.start, inversion)
                new_baseline_end = transform_point(line.baseline.end, inversion)

                lines.append(Line(line.text, BoundingBox(new_bb_start, new_bb_end, new_bb_inner_points), Baseline(new_baseline_start, new_baseline_end), None))

        new_dataset.add_page(Page(page_id + ".jpg_rec", lines))

    print()

    return new_dataset


def main():
    args = parse_args()

    dataset = Dataset(args.input, lazy=True)
    print(dataset)

    process_dataset(dataset, args.logs).save(args.output)

    return 0


if __name__ == "__main__":
    sys.exit(main())
