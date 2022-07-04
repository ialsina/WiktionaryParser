# TO BE DEPRECATED

import logging, inspect, os

from wiktionaryparser.definitions import PATH_LOG, PATH_DEBUG

_debugger = logging.getLogger(__name__ + '.debugger')
_debugger.setLevel(logging.DEBUG)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
console_formatter = logging.Formatter('%(asctime)s | %(message)s', '%H:%M:%S')
console_handler.setFormatter(console_formatter)

file_handler = logging.FileHandler(PATH_DEBUG, 'w')
file_handler.setLevel(logging.DEBUG)
file_formatter = logging.Formatter('%(asctime)s | %(message)s', '%H:%M:%S')
file_handler.setFormatter(file_formatter)

_debugger.addHandler(file_handler)

_parsing_logger = logging.getLogger(__name__)
_parsing_logger.setLevel(logging.ERROR)
_parsing_logger.setLevel(logging.WARNING)
file_handler = logging.FileHandler(PATH_LOG, 'r')
_parsing_logger.addHandler(file_handler)
_parsing_logger.addHandler(console_handler)

def autolog(message, arg=1):
    "Automatically log the current function details."
    # Get the previous frame in the stack, otherwise it would
    # be this function!!!
    func = inspect.currentframe().f_back.f_code

    if arg == 0:
        return

    if arg == 2:
        message = '\n\t\t{}\n'.format(message)

    elif arg ==3:
        underline = '='*len(message)
        message = '\n\n\t{}\n\t{}\n\t{}\n\n'.format(underline, message, underline)

    message = str(message)

    # Dump the message + the name of this function to the log.
    _debugger.debug('{2:<20s} {3:>4d} | {1:<30s} | {0:s}'.format(
        message,
        func.co_name,
        os.path.split(func.co_filename)[1],
        func.co_firstlineno
    ))


def errorlog(exception):
    func = inspect.currentframe().f_back.f_code
    message = exception.message.replace("\n", " ")
    errlogger.error('{0:40s} {1:>30s}'.format(message, func.co_name))


def clearlog():
    with open(PATH_LOG, 'w') as f:
        pass
    with open(PATH_ERRLOG, 'w') as f:
        pass