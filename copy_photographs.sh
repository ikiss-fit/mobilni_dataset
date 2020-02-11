#!/usr/bin/env bash

python3 copy_photographs.py \
    --input=/home/ikiss/Documents/Datasets/mobilni_dataset/_WEB/UNTRANSFORMED/xml/ \
    --output=/home/ikiss/Documents/Datasets/mobilni_dataset/_WEB/UNTRANSFORMED/photos/ \
    --translation-file=/mnt/matylda1/hradis/Datasets/CNN-Deconvolution/DATA/allFiles.txt \
    --rectified-photos-path=/home/ikiss/Documents/Datasets/mobilni_dataset/_WEB/TRANSFORMED/photos/ \
    --original-photos-path=/mnt/matylda1/hradis/Datasets/CNN-Deconvolution/DATA \
    --logs=/home/ikiss/Documents/Datasets/mobilni_dataset/LOGS/ \
