import logging, inspect, os

from wiktionaryparser.definitions import PATH_LOG, PATH_ERRLOG

logger = logging.getLogger('log')
logger.setLevel(logging.DEBUG)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
console_formatter = logging.Formatter('%(asctime)s | %(message)s', '%H:%M:%S')
console_handler.setFormatter(console_formatter)

file_handler = logging.FileHandler(PATH_LOG, 'a')
file_handler.setLevel(logging.DEBUG)
file_formatter = logging.Formatter('%(asctime)s | %(message)s', '%H:%M:%S')
file_handler.setFormatter(file_formatter)

logger.addHandler(file_handler)

errlogger = logging.getLogger('error')
errlogger.setLevel(logging.ERROR)
errfile_handler = logging.FileHandler(PATH_ERRLOG, 'a')
errlogger.addHandler(errfile_handler)

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
    logger.debug('{2:<20s} {3:>4d} | {1:<30s} | {0:s}'.format(
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