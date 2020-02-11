import os
import sys
import argparse
from transcription import Transcription
from result import Status, Result
from eval_data import EvalData


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--transcriptions', help='Path to transcriptions file.', required=True)
    parser.add_argument('-g', '--ground-truth', help='Path to ground truth file.', required=True)
    args = parser.parse_args()
    return args


def load_transcriptions(path):
    transcriptions = {}
    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            if len(line) > 0:
                line_parts = line.split(maxsplit=1)
                line_parts_count = len(line_parts)
                if line_parts_count > 0:
                    file = line_parts[0]
                    transcription = ""

                    if line_parts_count == 2:
                        transcription = line_parts[1]

                    transcriptions[file] = transcription

    return Result(Status.SUCCESS, transcriptions)


def test(transcriptions, ground_truths):
    lines_result = process_lines(transcriptions, ground_truths)
    if lines_result.status == Status.FAILURE:
        return lines_result

    lines = lines_result.data
    if len(lines) == 0:
        return Result(Status.FAILURE, None, "There are no lines to calculate CER and WER.")

    cer = float(sum([line.char_distance() for line in lines])) / sum([len(line.ground_truth) for line in lines])
    wer = float(sum([line.word_distance() for line in lines])) / sum([len(line.ground_truth.split()) for line in lines])

    return Result(Status.SUCCESS, (cer, wer))


def process_lines(transcriptions, ground_truths):
    missing = []
    lines = []

    for index, image_id in enumerate(ground_truths):
        ground_truth = ground_truths[image_id]
        transcription = ""

        if image_id in transcriptions:
            transcription = transcriptions[image_id]
        else:
            missing.append(image_id)

        line = Transcription(image_id, ground_truth, transcription)

        lines.append(line)

    message = "Missing transcriptions for lines: '{lines}'.".format(lines="', '".join(missing))

    return Result(Status.SUCCESS, lines, message=message)


def test_files(transcriptions_path: str, ground_truths_path: str) -> Result:
    '''
    Args:
        transcriptions_path (str): Path to transcription file.
        ground_truths_path (str): Path to ground-truth file.

    Returns:
        Result: Result object with success status and optionally with data or with detailed information about failure.
    '''
    transcriptions_result = load_transcriptions(transcriptions_path)
    if transcriptions_result.status == Status.FAILURE:
        return transcriptions_result

    ground_truths_result = load_transcriptions(ground_truths_path)
    if ground_truths_result.status == Status.FAILURE:
        return ground_truths_result

    result = test(transcriptions_result.data, ground_truths_result.data)

    return result


def main():
    args = parse_arguments()

    result = test_files(args.transcriptions, args.ground_truth)
    if result.status == Status.SUCCESS:
        cer, wer = result.data
        print("CER: {cer}\nWER: {wer}".format(cer=cer, wer=wer))
    else:
        print(result)

    return 0


if __name__ == "__main__":
    sys.exit(main())
