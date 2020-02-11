import decoding


class Transcription:
    def __init__(self, file, ground_truth, transcription):
        self.file = file
        self.ground_truth = ground_truth
        self.transcription = transcription

    def cer(self):
        return float(self.char_distance()) / len(self.ground_truth)

    def wer(self):
        return float(self.word_distance()) / len(self.ground_truth.split())

    def char_distance(self):
        return decoding.levenshtein_distance([c for c in self.transcription], [c for c in self.ground_truth])

    def word_distance(self):
        return decoding.levenshtein_distance(self.transcription.split(), self.ground_truth.split())
