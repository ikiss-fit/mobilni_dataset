#!/usr/bin/env bash

python3 translate.py \
    --lines="translated.txt" \
    --translations="test_translations.txt" \
    --output="translated_reverse.txt" \
    --reverse
