import sys
import cv2
from os.path import join
import os

from dataset import Dataset


def parse_arguments():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--dataset", help="Path to dataset.", required=True)
    parser.add_argument("-i", "--images", help="Path to images.", required=True)
    parser.add_argument("-l", "--logs", help="Path to logs.", required=False, default=None)
    parser.add_argument("-p", "--prefix", help="Preifx.", required=False, default="")
    parser.add_argument("-b", "--bbox-translation", help="Translate bounding-boxes.", required=False, default=False)
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

    offset_top = height * 0.1
    offset_left = width * 0.1

    return int(offset_left), int(offset_left)


def draw_bounding_box(image, bounding_box, color, thickness, top_offset, left_offset):
    top_left_corner = bounding_box.start.get_tuple(top_offset, left_offset)
    bottom_right_corner = bounding_box.end.get_tuple(top_offset, left_offset)

    if len(bounding_box.inner_points) > 0:
        bottom_left_corner = bounding_box.inner_points[0].get_tuple(top_offset, left_offset)
        top_right_corner = bounding_box.inner_points[1].get_tuple(top_offset, left_offset)

        cv2.line(image, top_left_corner, top_right_corner, color, thickness)
        cv2.line(image, top_left_corner, bottom_left_corner, color, thickness)
        cv2.line(image, top_right_corner, bottom_right_corner, color, thickness)
        cv2.line(image, bottom_left_corner, bottom_right_corner, color, thickness)
    else:
        cv2.rectangle(image, top_left_corner, bottom_right_corner, color, thickness)


def draw_information(image, page, bbox_translation):
    top_offset = 0
    left_offset = 0

    if bbox_translation:
        top_offset, left_offset = update_offsets(image)

    for line in page.lines:
        if line.bounding_box is not None:
            draw_bounding_box(image, line.bounding_box, (255, 0, 0), 3, top_offset, left_offset)

            if line.baseline is not None:
                cv2.line(image, line.baseline.start.get_tuple(top_offset, left_offset), line.baseline.end.get_tuple(top_offset, left_offset), (0, 255, 0), 3)

    return image


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


def show_images(dataset, images_folder, logs_folder=None, bbox_translation=False, prefix=""):
    cv2.namedWindow('image', cv2.WINDOW_GUI_EXPANDED)

    image_names = get_images(images_folder)

    translation = {}
    if logs_folder is not None:
        translation = translate_logs(logs_folder)

    for image_name in image_names:
        id = image_name[:image_name.index(".")]
        page_id = None

        print("Dataset contains id '{id}': {result}".format(id=id, result=id in dataset.pages))

        if id in dataset.pages:
            page_id = id
        elif id in translation:
            page_id = translation[id]
            print(id, "translated to", page_id)
        else:
            continue

        if (id.startswith(prefix) or page_id.startswith(prefix)) and page_id in dataset.pages:
            page = dataset.get_page(page_id)
            if page is None:
                print("Could not get page with id:" + page_id)
                continue

            image = load_image(images_folder, image_name)

            if image is not None:
                image = draw_information(image, page, bbox_translation)
                cv2.imshow('image', image)

                next_image = False
                close = False
                while not next_image and not close:
                    pressed_key = cv2.waitKey(100) & 0xFF

                    # ESC -> stop
                    if pressed_key == 27:
                        close = True

                    # ENTER -> show next image
                    elif pressed_key == ord("\n") or pressed_key == ord("\r"):
                        next_image = True

                    # 'p' -> print current page id
                    elif pressed_key == ord("p"):
                        print(page_id)

                    if cv2.getWindowProperty('image', cv2.WND_PROP_VISIBLE) < 1:
                        close = True

                if close:
                    break

            else:
                pass

    cv2.destroyAllWindows()

def main():
    args = parse_arguments()

    dataset = Dataset(args.dataset, lazy=True)
    print(dataset)

    show_images(dataset, args.images, args.logs, args.bbox_translation, args.prefix)

    return 0


if __name__ == "__main__":
    sys.exit(main())