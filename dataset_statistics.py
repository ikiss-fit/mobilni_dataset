import os
import sys
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
import os
import exifread

from dataset import Dataset
from typing import List, Dict, Tuple, Optional


def parse_arguments():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--dataset", help="Path to dataset.", required=False)
    parser.add_argument("-c", "--crops", help="Path to cropped files.", required=False)
    parser.add_argument("--lines", help="Path to lines file.", required=False)
    parser.add_argument("-l", "--logs", required=False)
    parser.add_argument("--devices", required=False)
    parser.add_argument("--exif-data", required=False)
    parser.add_argument("--count-lines", help="Count lines of loaded dataset.", required=False, action="store_true")
    parser.add_argument("-s", "--show-charts", help="Show charts.", required=False, default=False, action="store_true")
    args = parser.parse_args()
    return args


def get_id_from_log(log_name, logs_folder):
    with open(os.path.join(logs_folder, log_name)) as f:
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


def show_charts(dataset: Dataset) -> None:
    lengths = dataset.get_lengths()
    show_histogram(lengths, "Histogram of lines per page", "Number of lines", "Number of templates", bin_labels=True)


def show_histogram(values: List[int], title, x_label, y_label="Count", xticks=None, logarithmic_scale=False, bins=None, bin_labels=False, aggregate_last=False) -> None:
    if bins is None:
        bins = np.arange(min(values), max(values) + 2)
    # elif aggregate_last:
    #     values = np.clip(values, bins[0], bins[-1])

    if xticks is None:
        xticks = bins

    n, bins, patches = plt.hist(values, bins=bins, rwidth=0.95)

    if logarithmic_scale:
        plt.xscale("log")
    else:
        plt.axis([0, bins[-1], 0, max(n)])

    plt.title(title)
    plt.xlabel(x_label)
    plt.ylabel(y_label)

    if bin_labels:
        bins_labels(bins, xticks)
    else:
        plt.xticks(bins, xticks)

    plt.show()


def bins_labels(bins, ticks, **kwargs):
    bin_w = (max(bins) - min(bins)) / (len(bins) - 1)
    plt.xticks(np.arange(min(bins)+bin_w/2, max(bins), bin_w), ticks, **kwargs)
    plt.xlim(bins[0], bins[-1])


def print_statistics(dataset: Dataset) -> None:
    print("Lengths: ", dataset.get_lengths())


def get_image_widths(crops_path):
    images = [f for f in os.listdir(crops_path) if f.endswith(".jpg")]
    widths = []
    for image in images:
        img = Image.open(os.path.join(crops_path, image))
        width, _ = img.size
        widths.append(width)

    return widths


def show_crops_charts(crops_path):
    image_widths = get_image_widths(crops_path)
    show_histogram(image_widths, "Image width histogram", x_label="Image width")  # , logarithmic_scale=True, bins=[1, 10, 100, 1000, 10000])


def print_photograph_statistics(lines_path, translation):
    used_templates_lines = {}
    used_templates_pages = {}
    pages_set = set()

    images = []

    with open(lines_path, "r") as f:
        for line in f:
            images.append(line.split(".", maxsplit=1)[0])

    for image in images:
        if image in translation:
            template_id = translation[image]

            if template_id in used_templates_lines:
                used_templates_lines[template_id] += 1
            else:
                used_templates_lines[template_id] = 1

            if image not in pages_set:
                pages_set.add(image)
                if template_id in used_templates_pages:
                    used_templates_pages[template_id] += 1
                else:
                    used_templates_pages[template_id] = 1

        else:
            print("Id", image, "not found in translation dictionary.")

    # print("Used templates (lines):", len(used_templates_lines))
    # print("Used templates (pages):", len(used_templates_pages))

    # [print(t) for t in used_templates_pages]

    return used_templates_lines, used_templates_pages


def load_devices(path):
    devices = {}

    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            photograph_id, path_to_photograph = line.split(maxsplit=1)
            devices[photograph_id] = path_to_photograph

    return devices


def devices_statistics(dataset, devices, path, exif_data=None):
    device_statistics = {}

    device_name_translation = {
        "Samsung GT-I9100": "Samsung Galaxy S II",
        "GT-I9100 Samsung": "Samsung Galaxy S II",
        "SAMSUNG SM-G900F": "Samsung Galaxy S5",
        "samsung SM-G900F": "Samsung Galaxy S5",
        "SAMSUNG             GT-S8530":  "Samsung Wave II",
        "SAMSUNG GT-S8530": "Samsung Wave II",
        "HUAWEI ALE-L21": "Huawei P8 Lite",
        "LG Electronics LG-D802": "LG G2",
        "LG Electronics LG-H815": "LG G4",
        "LG-H815 LG Electronics": "LG G4",
        "LGE Nexus 4": "LG Nexus 4",
        "Nexus 4 LGE": "LG Nexus 4",
        "LGE Nexus 5": "LG Nexus 5",
        "Nexus 5 LGE": "LG Nexus 5",
        "Motorola XT1032": "Motorola Moto G",
        "BlackBerry BlackBerry Unknown": "BlackBerry",
        "HTC HTC Desire S": "HTC Desire S",
        "Apple iPhone 5s": "Apple iPhone 5S",
        "Microsoft Lumia 535 Dual SIM": "Microsoft Lumia 535"
    }

    total = len(dataset.pages)

    for index, page in enumerate(dataset.pages):
        print("\r{current}/{total} ".format(current=index, total=total), end="")

        if page in devices:
            relative_path_to_photograph = devices[page]
            path_to_photograph = os.path.join(path, relative_path_to_photograph)

            device = "Unknown"

            if exif_data is not None:
                try:
                    device = exif_data[path_to_photograph]
                except:
                    print("NOT FOUND:", path_to_photograph)
            else:
                with open(path_to_photograph, "rb") as f:
                    tags = exifread.process_file(f)

                    try:
                        device = tags["Image Make"].values + " " + tags["Image Model"].values
                    except:
                        pass

            try:
                device = device_name_translation[device]
            except:
                pass

            if device in device_statistics:
                device_statistics[device] += 1
            else:
                device_statistics[device] = 1

    # print(device_statistics)

    return device_statistics


def show_devices_chart(device_statistics, sort=True):
    devices = []
    counts = []

    if sort:
        for device in sorted(list(device_statistics.items()), key=lambda pair: pair[1]):
            devices.append(device[0])
            counts.append(device[1])
    else:
        devices = list(device_statistics.keys())
        counts = list(device_statistics.values())

    show_horizontal_bar_chart(devices, counts, x_label="Number of photographs", title="Device statistics")


def show_horizontal_bar_chart(labels, values, x_label="Count", title="Chart", show_values=True):
    fig, ax = plt.subplots()

    if show_values:
        for i, v in enumerate(values):
            plt.text(v, i, " " + str(v), color='#1f77b4', va='center', fontweight='bold')

    y_pos = np.arange(len(labels))

    ax.barh(y_pos, values, align='center')
    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels)
    ax.invert_yaxis()  # labels read top-to-bottom
    ax.set_xlabel(x_label)
    ax.set_xlim(0, 4200)
    ax.set_title(title)

    plt.subplots_adjust(left=0.4, right=0.6, top=0.7, bottom=0.3)
    plt.margins(y=0.01)
    plt.show()


def load_exif(exif_data_path):
    exif = {}

    with open(exif_data_path, "r") as f:
        for line in f:
            line = line.strip()
            if len(line) > 0:
                line_splitted = line.split(maxsplit=1)
                if len(line_splitted) == 2:
                    exif[line_splitted[0]] = line_splitted[1]
                else:
                    exif[line_splitted[0]] = "Unknown"

    return exif


def show_template_usage_photographs(values, max_value=25):
    values = np.clip(values, min(values), max_value)

    bins = np.arange(1, max_value + 2)
    ticks = list(map(str, bins[:-1]))
    ticks[-1] += "+"

    show_histogram(values, "Histogram of template usage (photographs)", "Number of photographs",
                   "Number of templates", bins=bins, xticks=ticks, bin_labels=True)


def show_template_usage_lines(values, max_value=1100):
    values = np.clip(values, min(values), max_value)

    bins = np.arange(0, max_value + 2, 100)
    ticks = list(map(str, bins))
    ticks[-1] = "2500"

    show_histogram(values, "Histogram of template usage (lines)", "Number of lines",
                   "Number of templates", logarithmic_scale=False,
                   bins=bins, xticks=ticks)

    ticks = ["1-99", "100-199", "200-299", "300-399", "400-499", "500-599", "600-699", "700-799", "800-899", "900-999", "1000+"]

    show_histogram(values, "Histogram of template usage (lines)", "Number of lines",
                   "Number of templates", logarithmic_scale=False,
                   bins=bins, xticks=ticks, bin_labels=True)

def main():
    args = parse_arguments()

    if args.dataset is not None:
        dataset = Dataset(args.dataset, lazy=True)

        print(dataset)

        if args.devices is not None:
            exif_data = None
            if args.exif_data is not None:
                exif_data = load_exif(args.exif_data)

            device_statistics = devices_statistics(dataset, load_devices(args.devices), os.path.dirname(args.devices), exif_data=exif_data)

            if args.show_charts:
                show_devices_chart(device_statistics)
            else:
                for device in device_statistics:
                    print("{device}: {count}".format(device=device, count=device_statistics[device]))

                print("Total:", sum(list(device_statistics.values())))
        else:
            if args.count_lines:
                print("Number of lines:", dataset.count_lines())

            if args.show_charts:
                show_charts(dataset)
            else:
                print_statistics(dataset)

    if args.crops is not None:
        show_crops_charts(args.crops)

    if args.lines is not None and args.logs is not None:
        translation = translate_logs(args.logs)
        used_templates_lines, used_templates_pages = print_photograph_statistics(args.lines, translation)

        if args.show_charts:

            show_template_usage_lines(list(used_templates_lines.values()))
            show_template_usage_photographs(list(used_templates_pages.values()))


    return 0


if __name__ == "__main__":
    sys.exit(main())
