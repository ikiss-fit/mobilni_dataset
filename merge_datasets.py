import logging
import os
import sys
from typing import Tuple, List, Optional
from time import gmtime, strftime
import decoding
from dataset import Dataset, Page, Line
import cv2


def parse_arguments():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-a', '--abbyy-folder', help='Path to abbyy input files.', required=True)
    parser.add_argument('-t', '--tesseract-folder', help='Path to tesseract input files.', required=True)
    parser.add_argument('-o', '--output-folder', help='Path to output folder.', required=True)
    parser.add_argument('-i', '--images-folder', help="Path to images folder.", required=False, default=None)
    args = parser.parse_args()
    return args


def merge_lines(line1: Line, line2: Line) -> Line:
    new_line = Line(line1.text, None, None, None)

    if line1.bounding_box is not None:
        new_line.bounding_box = line1.bounding_box
    elif line2.bounding_box is not None:
        new_line.bounding_box = line2.bounding_box

    if line1.baseline is not None:
        new_line.baseline = line1.baseline
    elif line2.baseline is not None:
        new_line.baseline = line2.baseline

    if line1.confidence is None:
        new_line.confidence = line2.confidence
    elif line2.confidence is None:
        new_line.confidence = line1.confidence
    else:
        confidences = [line1.confidence, line2.confidence]
        new_line.confidence = sum(confidences) / len(confidences)

    return new_line


def get_same_lines(aligned_lines: List[Tuple[Line, Line]]) -> List[Line]:
    # result = [line1 for (line1, line2) in aligned_lines if line1 == line2]
    result = []

    for aligned_pair in aligned_lines:
        line1 = aligned_pair[0]
        line2 = aligned_pair[1]

        logging.debug(line1)
        logging.debug(line2)

        if line1 == line2:
            result.append(merge_lines(line1, line2))
            logging.debug("EQUAL")
        else:
            logging.debug("DIFFERENT")

        logging.debug("==========================================================")

    return result


def intersect_pages(page1: Page, page2: Page) -> Optional[Page]:
    lines1 = page1.lines
    lines2 = page2.lines

    logging.debug("##########################################################")
    logging.debug("Page ID: " + page1.id)
    logging.debug("##########################################################")

    aligned_lines = decoding.levenshtein_alignment(lines1, lines2)

    same_lines = get_same_lines(aligned_lines)

    if len(same_lines) == 0:
        return None

    return Page(page1.id, same_lines)


def merge_datasets(dataset1: Dataset, dataset2: Dataset) -> Dataset:
    result = Dataset()

    for id in dataset1.pages:
        if id in dataset2.pages:
            page1 = dataset1.pages[id]
            page2 = dataset2.pages[id]

            page = intersect_pages(page1, page2)

            if page is not None:
                result.add_page(page)

    return result


def indent_dataset(merged_dataset, images_folder):
    for page_id in merged_dataset.pages:
        img_path = os.path.join(images_folder, page_id + ".png")
        img = cv2.imread(img_path)
        if img is not None:
            _, width, _ = img.shape
            offset = int(width * 0.1)

            page = merged_dataset.pages[page_id]
            for line in page.lines:
                if line.bounding_box is not None:
                    line.bounding_box.start.x += offset
                    line.bounding_box.start.y += offset
                    line.bounding_box.end.x += offset
                    line.bounding_box.end.y += offset

                if line.baseline is not None:
                    line.baseline.start.x += offset
                    line.baseline.start.y += offset
                    line.baseline.end.x += offset
                    line.baseline.end.y += offset

                    for point in line.baseline.inner_points:
                        point.x += offset
                        point.y += offset
        else:
            print("could not read file {path}".format(path=img_path))


def main():
    args = parse_arguments()
    logging.basicConfig(filename="merge." + strftime("%Y-%m-%d_%H-%M-%S", gmtime()) + ".log", level=logging.DEBUG)

    abbyy_dataset = Dataset(args.abbyy_folder)
    tesseract_dataset = Dataset(args.tesseract_folder)

    merged_dataset = merge_datasets(abbyy_dataset, tesseract_dataset)

    if args.images_folder is not None:
        print("indenting")
        indent_dataset(merged_dataset, args.images_folder)

    merged_dataset.save(args.output_folder)
    print("Dataset saved to " + args.output_folder)

    return 0


if __name__ == "__main__":
    sys.exit(main())
