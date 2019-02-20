import os
import re

class LineTranscription:
    def __init__(self, path, ler, loss, ground_truth, transcription):
        self.path = path
        self.filename = os.path.basename(path)
        self.ler = ler
        self.loss = loss
        self.ground_truth = ground_truth
        self.transcription = transcription

    @staticmethod
    def parse(line: str):
        pattern = "([A-Za-z0-9_.]+)\t([0-9]*\.[0-9]+|[0-9]+)\t([0-9]*\.[0-9]+|[0-9]+|[0-9]*\.[0-9]+[e]{0,1}[+-]{0,1}[0-9]+)\t'(.*)'\t'(.*)'"
        match = re.match(pattern, line)
        if match:
            return LineTranscription(
                match.groups()[0],
                float(match.groups()[1]),
                float(match.groups()[2]),
                match.groups()[3],
                match.groups()[4])

        return None

    def loss_normalized(self):
        loss_normalized = self.loss

        if self.transcription is not None and len(self.transcription) > 0:
            loss_normalized = float(self.loss)/len(self.transcription)

        return loss_normalized

    def __str__(self, normalized_loss=False, rich=False):
        if rich:
            return 'Filename: {filename}\nLER: {ler}\nLOSS: {loss} ({loss_normalized})\nGround-truth: ' \
                   '{ground_truth}\nTranscription: {transcription}'.\
                format(filename=self.filename,
                       ler=self.ler,
                       loss=self.loss,
                       loss_normalized=self.loss_normalized(),
                       ground_truth=self.ground_truth,
                       transcription=self.transcription)

        if normalized_loss:
            return "{filename}\t{ler}\t{loss}\t'{ground_truth}'\t'{transcription}'".format(filename=self.filename,
                                                                                           ler=self.ler,
                                                                                           loss=self.loss_normalized(),
                                                                                           ground_truth=self.ground_truth,
                                                                                           transcription=self.transcription)

        return "{filename}\t{ler}\t{loss}\t'{ground_truth}'\t'{transcription}'".format(filename=self.filename,
                                                                                       ler=self.ler, loss=self.loss,
                                                                                       ground_truth=self.ground_truth,
                                                                                       transcription=self.transcription)
