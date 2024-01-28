class TranslationParsingError(Exception):
    reason = "unknown"

    def __init__(self, info=None, show_html=False, *args, **kwargs):
        if info is None:
            info = {}
        self.info = info
        self.args = args
        self.kwargs = kwargs
        self.show_html = show_html
        # self.message = "Error in word: {}.\n" \
        #               "Impossible to extract translation in: {}.\n" \
        #               "Reason: {}.".format(self.word, self.text, self.reason)

        super().__init__(self.message)

    @property
    def message(self):
        msg = ''
        if self.info:
            msg += 'In '
            if self.info.get("word"):
                msg += 'WORD:"{}", '.format(self.info.get("word"))
            if self.info.get("sense"):
                msg += 'SENSE:"{}", '.format(self.info.get("sense"))
            if self.info.get("language"):
                msg += 'LANG:"{}", '.format(self.info.get("language"))
            if self.info.get("text"):
                msg += 'the TEXT:"{}", '.format(self.info.get("text"))
            msg += 'i'
        else:
            msg += 'I'
        msg += 't is impossible to extract translation. ' \
               'REASON:"{}"'.format(self.reason)
        if self.show_html and self.info.html:
            msg += '\n\t' + self.info.html.prettify()
        return msg


class SenseLocationError(TranslationParsingError):
    def __init__(self, info=None, *args, **kwargs):
        super().__init__(info, *args, **kwargs)


class EmptySenseError(TranslationParsingError):
    reason = "No translations in current 'sense'"
    def __init__(self, info=None, *args, **kwargs):
        super().__init__(info, *args, **kwargs)


class MultipleTablesError(TranslationParsingError):
    reason = "Multiple tables or table bodies in 'sense'"

    def __init__(self, info=None, *args, **kwargs):
        super().__init__(info, *args, **kwargs)


class ZeroTablesError(TranslationParsingError):
    reason = "Zero tables or table bodies in 'sense'"

    def __init__(self, info=None, *args, **kwargs):
        super().__init__(info, *args, **kwargs)


class MissingColonError(TranslationParsingError):
    reason = "Missing colon (:)"

    def __init__(self, info=None, *args, **kwargs):
        super().__init__(info, *args, **kwargs)


class BadItemsError(TranslationParsingError):
    reason = "Bad items in line: missing comma + space"

    def __init__(self, info=None, *args, **kwargs):
        super().__init__(info, *args, **kwargs)


class ZeroLengthListError(TranslationParsingError):
    reason = "The translation yields a list of zero elements"

    def __init__(self, info=None, *args, **kwargs):
        super().__init__(info, *args, **kwargs)

# TO BE DEPRECATED
class ExceptionInfoPacker:
    def __init__(self, exception, info=None):
        if info is None:
            info = {}
        self.exception = exception
        self.word = info.get('word')
        self.sense = info.get('sense')
        self.lang = info.get('lang')
        self.text = info.get('text')
        self.info = info

    def __str__(self):
        msg = 'In '
        if self.word:
            msg += f'WORD:{self.word}, '
        if self.sense:
            msg += f'SENSE:{self.sense}, '
        if self.lang:
            msg += f'LANG:{self.lang}, '
        if self.text:
            msg += f'the TEXT: "{self.text}" arises the following exception: '
        else:
            msg += f'the following exception arises:\n\t'
        msg += str(self.exception)
        return msg
