import logging, inspect, os

from wiktionaryparser.definitions import PATH_LOG

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

def autolog(message, arg=1):
    "Automatically log the current function details."
    import inspect, logging
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

def clearlog():
    with open('log.txt', 'w') as f:
        pass