import sys
import logging
import sys
from typing import Tuple, List, Optional

import decoding
from dataset import Dataset, Page, Line


def parse_arguments():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-a', '--abbyy-folder', help='Path to abbyy input files.', required=True)
    parser.add_argument('-t', '--tesseract-folder', help='Path to tesseract input files.', required=True)
    parser.add_argument('-o', '--output-folder', help='Path to output folder.', required=True)
    args = parser.parse_args()
    return args


def get_same_lines(aligned_lines: List[Tuple[Line, Line]]) -> List[Line]:
    # result = [line1 for (line1, line2) in aligned_lines if line1 == line2]
    result = []

    for aligned_pair in aligned_lines:
        line1 = aligned_pair[0]
        line2 = aligned_pair[1]

        logging.debug(line1)
        logging.debug(line2)

        if line1 == line2:
            result.append(line1)
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


def print_statistics(abbyy_dataset, tesseract_dataset, merged_dataset):
    print("ABBYY")
    print(abbyy_dataset)
    print()
    print("TESSERACT")
    print(tesseract_dataset)
    print()
    print("MERGED DATASET")
    print(merged_dataset)


def main():
    args = parse_arguments()
    logging.basicConfig(filename='merge.log',level=logging.DEBUG)

    abbyy_dataset = Dataset(args.abbyy_folder)
    tesseract_dataset = Dataset(args.tesseract_folder)

    merged_dataset = merge_datasets(abbyy_dataset, tesseract_dataset)

    print_statistics(abbyy_dataset, tesseract_dataset, merged_dataset)

    merged_dataset.save(args.output_folder)
    print("\nDataset saved to " + args.output_folder)

    return 0


if __name__ == "__main__":
    sys.exit(main())
