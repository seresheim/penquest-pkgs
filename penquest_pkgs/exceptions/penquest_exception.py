

class PenQuestException(Exception):

    def __init__(self, code: int, message: str, *args, **kwargs):
        super(PenQuestException, self).__init__(*args, **kwargs)
        self.code = code
        self.message = message