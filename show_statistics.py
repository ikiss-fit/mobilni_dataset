import sys
import matplotlib.pyplot as plt
from dataset import Dataset
from typing import List, Dict, Tuple, Optional


def parse_arguments():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--dataset', help='Path to dataset.', required=True)
    parser.add_argument('-s', '--show-charts', help='Show charts.', required=False, default=False)
    args = parser.parse_args()
    return args


def print_statistics(dataset: Dataset) -> None:
    print(dataset)


def show_charts(dataset: Dataset) -> None:
    # lengths = dataset.get_lengths()
    # print("Lengths: " + str(lengths))
    # show_histogram(lengths)

    show_histogram([0, 2, 4, 6, 8, 10, 12])


def show_histogram(values: List[int]) -> None:
    n, bins, patches = plt.hist(values)

    plt.axis([0, len(values), 0, max(values)])
    plt.show()


def main():
    args = parse_arguments()

    dataset = Dataset(args.dataset)

    print_statistics(dataset)

    if args.show_charts:
        show_charts(dataset)

    return 0


if __name__ == "__main__":
    sys.exit(main())
