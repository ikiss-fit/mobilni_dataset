from shutil import copy

SOURCE_LINES_DIR="/home/ikiss/Documents/Datasets/mobilni_dataset/CROPPED_ALIGNED_RANSAC_ANGLE_48/lines.2018-12-17/"
SOURCE_LINES_FILE="/home/ikiss/Documents/Datasets/mobilni_dataset/DATASET/lines.all"
DESTINATION_LINES_DIR="/home/ikiss/Documents/Datasets/mobilni_dataset/_WEB/LINES/lines/"

with open(SOURCE_LINES_FILE, "r") as f:
    for line in f:
        line = line.strip()
        if len(line) > 0:
            filename = line.split()[0]

            copy(SOURCE_LINES_DIR + filename, DESTINATION_LINES_DIR + filename)
