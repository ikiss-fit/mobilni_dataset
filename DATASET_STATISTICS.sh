#!/usr/bin/env bash

# python3 dataset_statistics.py --lines=../../Datasets/mobilni_dataset/DATASET/lines.all --logs=../../Datasets/mobilni_dataset/LOGS/ --show-charts
# python3 dataset_statistics.py --dataset=../../Datasets/mobilni_dataset/RECTIFIED_DETECTED_LINES_USED/ --devices=/mnt/matylda1/hradis/Datasets/CNN-Deconvolution/DATA/allFiles.txt --exif-data=manufacturers.txt # --show-charts
python3 dataset_statistics.py --dataset=../../Datasets/mobilni_dataset/_WEB/TRANSFORMED/xml/ --devices=/mnt/matylda1/hradis/Datasets/CNN-Deconvolution/DATA/allFiles.txt --exif-data=manufacturers.txt # --show-charts
# python3 dataset_statistics.py --dataset=../../Datasets/mobilni_dataset/RECTIFIED_DETECTED_LINES_USED/ --show-charts