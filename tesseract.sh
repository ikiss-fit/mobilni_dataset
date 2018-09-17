#!/bin/bash

CONFIG_FILE="tesseract_config.ini"

for SOURCE_FILE in $1/*
do
    if [[ ${SOURCE_FILE} =~ ^.*\.png$ ]];
    then
        FILENAME=$(basename $SOURCE_FILE .png)
        DESTINATION_FILE=$2/$FILENAME
        `tesseract $SOURCE_FILE $DESTINATION_FILE hocr $CONFIG_FILE`
    fi
done
