
class TranslationParsingError(Exception):
    reason = "unknown"
    def __init__(self, word, text, *args):
        self.word = word
        self.text = text
        self.args = args
        self.message = "Error in word: {}.\n" \
                       "Impossible to extract translation in: {}.\n" \
                       "Reason: {}.".format(self.word, self.text, self.reason)
        super().__init__(self.message)

class MissingColonError(TranslationParsingError):
    reason = "Missing colon (:)"
    def __init__(self, word, text, *args):
        super().__init__(word, text, *args)

class BadItemsError(TranslationParsingError):
    reason = "Bad items in line: missing comma + space"
    def __init__(self, word, text, *args):
        super().__init__(word, text, *args)