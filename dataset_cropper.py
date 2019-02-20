import sys
import cv2
from os.path import join
import os
import random
import datetime
import numpy as np

from dataset import Dataset


CURRENT_DATE = datetime.datetime.now().strftime("%Y-%m-%d")


def parse_arguments():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--dataset", help="Path to dataset.", required=True)
    parser.add_argument("-i", "--images", help="Path to images.", required=True)
    parser.add_argument("-o", "--output", help="Path to output.", required=True)
    parser.add_argument("-l", "--logs", help="Path to logs.", required=False, default=None)
    parser.add_argument("-t", "--translate-bbox", help="Translate bounding-boxes.", required=False, default=False)
    parser.add_argument("-b", "--bbox-adjustment", help="Expand bounding-box relative to its height.", required=False, default=1.0)
    parser.add_argument("-r", "--ratio", help="Train and test ratio.", required=False, default=0.8)
    parser.add_argument("--target-height", help="Target height of the image", required=False, default=64, type=int)
    args = parser.parse_args()
    return args


def load_image(path, name):
    filename = join(path, name)

    image = cv2.imread(filename)

    if image is None:
        print(filename + ": NOT FOUND")
        image = cv2.imread(filename + ".png")

        if image is None:
            print(filename + ".png: NOT FOUND")
            image = cv2.imread(filename + ".jpg_rec.jpg")

            if image is None:
                print(filename + ".jpg_rec.jpg: NOT FOUND")

    return image


def update_offsets(image):
    height, width, channels = image.shape

    offset = width * 0.1

    return int(offset)


def save_image(image, path):
    cv2.imwrite(path, image)


def update_bounding_box(start, end, bbox_adjustment):
    bbox_height = end[1] - start[1]
    new_bbox_height = int(bbox_height * float(bbox_adjustment))

    bbox_offset = int((new_bbox_height - bbox_height) / 2)

    new_start = max(0, start[0] - bbox_offset), max(0, start[1] - bbox_offset)
    new_end = max(0, end[0] + bbox_offset), max(0, end[1] + bbox_offset)

    return new_start, new_end


def get_resized_dimension(image, target_height):
    height, width = image.shape[:2]
    target_width = int((target_height / float(height)) * width)

    return target_width, target_height


def crop_horizontal_bounding_box(image, line, offset, target_height, bbox_adjustment):
    start = line.bounding_box.start.get_tuple(offset, offset)
    end = line.bounding_box.end.get_tuple(offset, offset)

    start, end = update_bounding_box(start, end, bbox_adjustment)

    cropped_line = image[start[1]:end[1], start[0]:end[0]]
    target_dimensions = get_resized_dimension(cropped_line, target_height)

    cropped_line = cv2.resize(cropped_line, target_dimensions)

    return cropped_line


def crop_generic_bounding_box(image, line, offset, target_height, bbox_adjustment):
    top_left_corner = np.array(line.bounding_box.start.get_tuple(offset, offset))
    top_right_corner = np.array(line.bounding_box.inner_points[1].get_tuple(offset, offset))
    bottom_left_corner = np.array(line.bounding_box.inner_points[0].get_tuple(offset, offset))

    original_width = int(np.linalg.norm(top_right_corner - top_left_corner))
    original_height = int(np.linalg.norm(bottom_left_corner - top_left_corner))

    top_left_translated = np.array((0.0, 0.0))
    top_right_translated = np.array((original_width, 0.0))
    bottom_left_translated = np.array((0.0, original_height))
    bottom_right_translated = np.array((original_width, original_height))

    _, new_end = update_bounding_box(top_left_translated, bottom_right_translated, bbox_adjustment)

    adjustment = np.array((new_end[0] - bottom_right_translated[0], new_end[1] - bottom_right_translated[1]))

    top_left_translated += adjustment
    top_right_translated += adjustment
    bottom_left_translated += adjustment
    bottom_right_translated += adjustment

    source = np.array([top_left_corner, top_right_corner, bottom_left_corner]).astype(np.float32)
    target = np.array([top_left_translated, top_right_translated, bottom_left_translated]).astype(np.float32)

    T = cv2.getAffineTransform(source, target)

    cropped_line = cv2.warpAffine(image, T, tuple(np.array((original_width, original_height) + 2 * adjustment)))
    target_dimensions = get_resized_dimension(cropped_line, target_height)
    cropped_line = cv2.resize(cropped_line, target_dimensions)

    return cropped_line


def crop_image(image, page, original_name,  bbox_translation, output_folder, bbox_adjustment, target_height):
    offset = 0
    transcriptions = []

    if bbox_translation:
        offset = update_offsets(image)

    for index, line in enumerate(page.lines):
        if line.bounding_box is not None:
            if len(line.bounding_box.inner_points) > 0:
                cropped_line = crop_generic_bounding_box(image, line, offset, target_height, bbox_adjustment)
            else:
                cropped_line = crop_horizontal_bounding_box(image, line, offset, target_height, bbox_adjustment)

            filename = "{id}_l{index}.jpg".format(id=original_name, index=str(index).zfill(4))
            save_image(cropped_line, join(output_folder, "lines." + CURRENT_DATE, filename))

            transcriptions.append("{filename} {text}".format(filename=filename, text=line.text))

    return transcriptions


def get_images(images_folder):
    return [image_name for image_name in os.listdir(images_folder) if image_name.endswith(('.png', '.jpg'))]


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


def save_transcriptions(transcriptions, output_folder, ratio):
    random.shuffle(transcriptions)
    ratio = float(ratio)

    train_count = int(len(transcriptions) * ratio)

    train_transcriptions = transcriptions[:train_count]
    test_transcriptions = transcriptions[train_count:]

    with open(join(output_folder, CURRENT_DATE + ".trn"), "w") as f:
        f.writelines("\n".join(train_transcriptions))

    with open(join(output_folder, CURRENT_DATE + ".tst"), "w") as f:
        f.writelines("\n".join(test_transcriptions))


def crop_dataset(dataset, images_folder, output_folder, bbox_adjustment, ratio, target_height, logs_folder=None, bbox_translation=False):
    image_names = get_images(images_folder)
    transcriptions = []
    translation = {}

    processed_pages = 0

    if logs_folder is not None:
        translation = translate_logs(logs_folder)

    for image_name in image_names:
        id, _ = image_name.rsplit(".", maxsplit=1)
        page_id = None

        if id in dataset.pages:
            page_id = id
        elif id in translation:
            page_id = translation[id]
        else:
            # print("Could not find page for image:", image_name)
            continue

        if page_id in dataset.pages:
            processed_pages += 1

            print("\r{0:0.2f}%".format(float(processed_pages)/len(image_names) * 100), end="")

            page = dataset.pages[page_id]
            image = load_image(images_folder, image_name)

            if image is not None:
                image_transcriptions = crop_image(image, page, id, bbox_translation, output_folder, bbox_adjustment, target_height)
                transcriptions += image_transcriptions

        else:
            print("Page id", page_id, "was not found in the dataset")

    save_transcriptions(transcriptions, output_folder, ratio)

    print("\nProcessed pages:", processed_pages)
    print("Transcriptions:", len(transcriptions))


def create_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)


def main():
    args = parse_arguments()

    dataset = Dataset(args.dataset)
    print(dataset)

    create_dir(join(args.output, "lines." + CURRENT_DATE))

    crop_dataset(dataset, args.images, args.output, args.bbox_adjustment, args.ratio, args.target_height, args.logs, args.translate_bbox)

    return 0


if __name__ == "__main__":
    sys.exit(main())
