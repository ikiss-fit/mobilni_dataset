from result import ImmutableObject


class EvalData(ImmutableObject):
    def __init__(self, id, cer, wer):
        self.id = id
        self.cer = cer
        self.wer = wer

        self.lock()
