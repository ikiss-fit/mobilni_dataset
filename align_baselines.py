import itertools
import sys
import cv2
from os.path import join
import os
import numpy as np
from sklearn.linear_model import RANSACRegressor
from dataset import Dataset, Page, Line, Baseline, BoundingBox, Point


VERBOSE = False


def parse_arguments():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--bounding-box-dataset", help="Path to bounding-box dataset.", required=True)
    parser.add_argument("--baseline-dataset", help="Path to baseline dataset.", required=True)
    parser.add_argument("-o", "--output", help="Path to output.", required=True)
    parser.add_argument("-l", "--logs", help="Path to logs.", required=False, default=None)
    parser.add_argument("-m", "--max-angle", help="Maximum angle of baseline (in degrees)", type=float, required=False, default=5)
    args = parser.parse_args()
    return args


def get_id_from_log(log_name, logs_folder):
    with open(join(logs_folder, log_name)) as f:
        for line in f:
            if line.startswith("TEMPLATE"):
                return line[line.rindex("/") + 1:line.rindex(".")]

    return None


def translate_logs(logs_folder):
    log_names = [log_name for log_name in os.listdir(logs_folder) if log_name.endswith(".log")]

    translation = {}

    for log_name in log_names:
        page_id = get_id_from_log(log_name, logs_folder)

        if page_id is not None:
            translation[log_name[:log_name.index(".")]] = page_id

    return translation


def baseline_points_passing_bounding_box(bounding_box, baseline_points):
    passing_points = []

    for baseline_point in baseline_points:
        if bounding_box.start.x <= baseline_point.x <= bounding_box.end.x and bounding_box.start.y <= baseline_point.y <= bounding_box.end.y:
            passing_points.append(baseline_point)

    return passing_points


def get_passing_baselines(bounding_box, baselines):
    passing_baselines = []

    for baseline in baselines:
        baseline_points = [baseline.start] + [baseline.end] + baseline.inner_points
        if len(baseline_points_passing_bounding_box(bounding_box, baseline_points)) > 0:
            passing_baselines.append(baseline)

    return passing_baselines


def adjust_bounding_box(bounding_box):
    height = int(abs(bounding_box.end.y - bounding_box.start.y))
    width_coef = 0.1
    height_coef = 0.2

    # enlarge bounding box 10 % of its height to the left and to the right
    start_x = bounding_box.start.x - height * width_coef
    end_x = bounding_box.end.x + height * width_coef

    # expand bounding box 20 % down of its height
    start_y = bounding_box.start.y  # + height * height_coef
    end_y = bounding_box.end.y + height * height_coef

    return BoundingBox(start_x=start_x, start_y=start_y,
                       end_x=end_x, end_y=end_y)


def get_best_baseline(bounding_box_line, baselines):
    points = []

    bounding_box_adjusted = adjust_bounding_box(bounding_box_line.bounding_box)

    if VERBOSE:
        print("TEXT:", bounding_box_line.text)
        print("BOUNDING BOX:", bounding_box_line.bounding_box)

    baseline_counter = 0

    for baseline in baselines:
        baseline_points = baseline.inner_points  # + [baseline.start, baseline.end]
        passing_points = baseline_points_passing_bounding_box(bounding_box_adjusted, baseline_points)
        points += passing_points

    X = np.array([p.x for p in points]).reshape(-1, 1)
    y = np.array([p.y for p in points]).reshape(-1, 1)

    threshold = np.median(np.abs(y - np.median(y))) + 0.1
    ransac = RANSACRegressor(residual_threshold=threshold)

    try:
        ransac.fit(X, y)
    except ValueError:
        return None

    start_x = np.array([bounding_box_line.bounding_box.start.x]).reshape(-1, 1)
    end_x = np.array([bounding_box_line.bounding_box.end.x]).reshape(-1, 1)

    start_y = ransac.predict(start_x)
    end_y = ransac.predict(end_x)

    final_baseline = Baseline(start_x=int(start_x[0][0]), start_y=int(start_y[0][0]), end_x=int(end_x[0][0]), end_y=int(end_y[0][0]))

    if VERBOSE:
        print("NUMBER OF BASELINES:", baseline_counter)
        print("X", X)
        print("X.shape", X.shape)
        print("y", y)
        print("FINAL BASELINE:", final_baseline)

    return final_baseline


def get_baseline(bounding_box_line, baseline_page):
    baseline = None

    baselines = [l.baseline for l in baseline_page.lines]

    passing_baselines = get_passing_baselines(adjust_bounding_box(bounding_box_line.bounding_box), baselines)

    if len(passing_baselines) > 0:
        baseline = get_best_baseline(bounding_box_line, passing_baselines)

    return baseline


def line_intersection(line1, line2):
    xdiff = (line1[0][0] - line1[1][0], line2[0][0] - line2[1][0])
    ydiff = (line1[0][1] - line1[1][1], line2[0][1] - line2[1][1])

    def det(a, b):
        return a[0] * b[1] - a[1] * b[0]

    div = det(xdiff, ydiff)
    if div == 0:
        return None

    d = (det(*line1), det(*line2))
    x = det(d, xdiff) / div
    y = det(d, ydiff) / div
    return x, y


def align_bounding_box_to_baseline(bounding_box_line, baseline):
    top_offset = 0.8
    bottom_offset = 1 - top_offset

    # print("----")

    left_top = bounding_box_line.bounding_box.start.x, bounding_box_line.bounding_box.start.y
    right_top = bounding_box_line.bounding_box.end.x, bounding_box_line.bounding_box.start.y
    left_bottom = bounding_box_line.bounding_box.start.x, bounding_box_line.bounding_box.end.y
    right_bottom = bounding_box_line.bounding_box.end.x, bounding_box_line.bounding_box.end.y

    left_line = left_top, left_bottom
    right_line = right_top, right_bottom

    baseline_line = (baseline.start.x, baseline.start.y), (baseline.end.x, baseline.end.y)

    left_intersection = line_intersection(left_line, baseline_line)
    right_intersection = line_intersection(right_line, baseline_line)

    if left_intersection is None or right_intersection is None:
        return None, None

    start = np.array(left_intersection)
    end = np.array(right_intersection)

    # print("START", start)
    # print("END", end)

    vector = end - start

    # print("VECTOR", vector)

    normal_vector_up = np.array((-vector[1], vector[0]))
    normal_vector_down = np.array((vector[1], -vector[0]))

    # print("UP", normal_vector_up)
    # print("DOWN", normal_vector_down)

    normal_vector_up /= np.linalg.norm(normal_vector_up)
    normal_vector_down /= np.linalg.norm(normal_vector_down)

    # print("NORMALIZED UP", normal_vector_up)
    # print("NORMALIZED DOWN", normal_vector_down)

    bounding_box_height = int(abs(bounding_box_line.bounding_box.end.y - bounding_box_line.bounding_box.start.y))

    # print("BBOX HEIGHT", bounding_box_height)

    top_vector = normal_vector_up * bounding_box_height * top_offset
    bottom_vector = normal_vector_down * bounding_box_height * bottom_offset

    # print("TOP", top_vector)
    # print("BOTTOM", bottom_vector)

    # top_vector and bottom_vector must be subtracted because origin of the image coordinates is in the top left corner
    top_left_corner = start - top_vector
    top_right_corner = end - top_vector
    bottom_left_corner = start - bottom_vector
    bottom_right_corner = end - bottom_vector

    # print("TOP LEFT CORNER", top_left_corner)
    # print("BOTTOM RIGHT CORNER", top_left_corner)

    result_bounding_box = BoundingBox(start_x=int(top_left_corner[0]), start_y=int(top_left_corner[1]),
                               end_x=int(bottom_right_corner[0]), end_y=int(bottom_right_corner[1]))
    result_bounding_box.inner_points = [Point(x=int(bottom_left_corner[0]), y=int(bottom_left_corner[1])),
                                        Point(x=int(top_right_corner[0]), y=int(top_right_corner[1]))]

    result_baseline = Baseline(start_x=int(start[0]), start_y=int(start[1]), end_x=int(end[0]), end_y=int(end[1]))

    return result_bounding_box, result_baseline


def get_baseline_angle(baseline):
        x1, y1 = baseline.start.get_tuple()
        x2, y2 = baseline.end.get_tuple()

        dx = x2 - x1
        dy = y2 - y1

        p = np.array(dx + dy * 1j)

        return np.angle(p, deg=True)


def align_pages(baseline_page, bounding_box_page, max_angle):
    lines = []

    for index, bounding_box_line in enumerate(bounding_box_page.lines):
        # if baseline_page.id.startswith("b9687eff32a766d00d09769210749433") and index == 10:
        #     global VERBOSE
        #     VERBOSE = True
        # else:
        #     global VERBOSE
        #     VERBOSE = False

        baseline = get_baseline(bounding_box_line, baseline_page)

        if baseline is not None:
            bounding_box, baseline = align_bounding_box_to_baseline(bounding_box_line, baseline)
            if abs(get_baseline_angle(baseline)) < max_angle:
                if bounding_box is not None and baseline is not None:
                    lines.append(Line(bounding_box_line.text, bounding_box, baseline, bounding_box_line.confidence))

    return Page(baseline_page.id, lines)


def align_bboxes_and_baselines(bounding_box_dataset, baseline_dataset, max_angle, logs_folder, output_folder):
    result_dataset = Dataset()

    translation = {}
    if logs_folder is not None:
        translation = translate_logs(logs_folder)

    total_pages = len(baseline_dataset.pages)

    print("0/{total} (0.00 %)".format(total=total_pages), end='')

    for index, baseline_page_id_full in enumerate(baseline_dataset.pages):
        baseline_page_id = baseline_page_id_full.split(".")[0]
        bounding_box_page_id = translation[baseline_page_id]

        # print("BaselinePageID: {baseline_id} translated to BoundingBoxPageID: {bounding_box_id}".format(baseline_id=baseline_page_id, bounding_box_id=bounding_box_page_id))

        baseline_page = baseline_dataset.get_page(baseline_page_id_full + ".jpg_rec.xml")
        bounding_box_page = bounding_box_dataset.get_page(bounding_box_page_id)

        if baseline_page is None or bounding_box_page is None:
            continue

        result_page = align_pages(baseline_page, bounding_box_page, max_angle)

        result_dataset.add_page(result_page)

        if len(list(result_dataset.pages.keys())) > 100:
            result_dataset.save(output_folder)
            result_dataset = Dataset()

        print("\r{current}/{total} ({percentage:0.2f} %)".format(current=index+1, total=total_pages, percentage=float(index+1)/total_pages * 100), end='')

    print()

    result_dataset.save(output_folder)

    return result_dataset


def main():
    args = parse_arguments()

    bounding_box_dataset = Dataset(args.bounding_box_dataset)
    print("Bounding box dataset")
    print(bounding_box_dataset)

    baseline_dataset = Dataset(args.baseline_dataset, lazy=True)
    print("Baseline dataset")
    print(baseline_dataset)

    aligned_dataset = align_bboxes_and_baselines(bounding_box_dataset, baseline_dataset, args.max_angle, args.logs, args.output)
    # print("Aligned dataset")
    # print(aligned_dataset)
    #
    # aligned_dataset.save(args.output)
    print("Dataset saved to", args.output)

    aligned_dataset = Dataset(args.output)
    print("Aligned dataset")
    print(aligned_dataset)

    return 0


if __name__ == "__main__":
    sys.exit(main())
