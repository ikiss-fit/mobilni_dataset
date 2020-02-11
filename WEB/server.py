import os
import sys
import argparse
import uuid
import config_helper
import test_transcriptions

from typing import Optional
from flask import Flask, request, render_template
from eval_data import EvalData
from result import Result, Status

app = Flask(__name__, template_folder=".")

configuration = None


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config-file', required=True, help='Path to configuration file.')
    args = parser.parse_args()
    return args


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        file_path = save_file(request, "bmod_uploaded_transcription_file", configuration["BMOD"]["upload_path"])

        if file_path is not None:
            result = evaluate(file_path, configuration["BMOD"]["ground_truth_path"])
        else:
            result = Result(Status.FAILURE, None, "Could not save file from the request.")

        output = get_page(result)
    else:
        output = get_page()

    return output


def save_file(req, input_name, path):
    if not os.path.exists(path):
        os.makedirs(path)

    file_path = None
    name = uuid.uuid4().hex + ".txt"

    if input_name in req.files:
        file = req.files[input_name]
        file_path = os.path.join(path, name)
        file.save(file_path)

    return file_path


def evaluate(transcription_path, ground_truth_path):
    try:
        result = test_transcriptions.test_files(transcription_path, ground_truth_path)
        cer, wer = result.data
        result = Result(result.status, EvalData(transcription_path, cer, wer), result.message)
    except:
        result = Result(Status.FAILURE, "Something unexpectedly failed during evaluation.")

    return result


def get_page(result: Optional[Result] = None):
    if result is not None:
        if result.status == Status.SUCCESS:
            eval_data = result.data
            output = render_template('bmod.html', success=True, id=eval_data.id, cer=eval_data.cer, wer=eval_data.wer, message=result.message)
        else:
            output = render_template('bmod.html', success=False, message=result.message)
    else:
        output = render_template('bmod.html')

    return output


def main():
    args = parse_args()

    global configuration
    configuration = config_helper.parse_configuration(args.config_file)

    host = configuration["common"]["host"]
    port = configuration["common"]["port"]
    debug = configuration["common"]["debug"]
    app.run(host=host, port=port, debug=debug)


if __name__ == '__main__':
    sys.exit(main())
