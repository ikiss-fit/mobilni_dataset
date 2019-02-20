import sys
import matplotlib.pyplot as plt
import numpy as np

from dataset import Dataset
from typing import List, Dict, Tuple, Optional


def parse_arguments():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--dataset', help='Path to dataset.', required=True)
    parser.add_argument('-s', '--show-charts', help='Show charts.', required=False, default=False)
    args = parser.parse_args()
    return args


def show_charts(dataset: Dataset) -> None:
    lengths = dataset.get_lengths()
    show_histogram(lengths)


def show_histogram(values: List[int]) -> None:
    n, bins, patches = plt.hist(values, bins=np.arange(max(values) + 2))
    plt.axis([0, bins[-1], 0, max(n)])
    bins_labels(bins)
    plt.show()


def bins_labels(bins, **kwargs):
    bin_w = (max(bins) - min(bins)) / (len(bins) - 1)
    plt.xticks(np.arange(min(bins)+bin_w/2, max(bins), bin_w), bins, **kwargs)
    plt.xlim(bins[0], bins[-1])


def print_statistics(dataset: Dataset) -> None:
    print("Lengths: ", dataset.get_lengths())


def main():
    args = parse_arguments()

    dataset = Dataset(args.dataset)

    print(dataset)

    if args.show_charts:
        show_charts(dataset)
    else:
        print_statistics(dataset)

    return 0


if __name__ == "__main__":
    sys.exit(main())
