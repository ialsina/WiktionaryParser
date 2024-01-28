# Alternative solution:
# https://stackoverflow.com/questions/10973362/python-logging-function-name-file-name-line-number-using-a-single-file#10974508

import logging
from wiktionaryparser.definitions import PATH_LOG

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

file_handler = logging.FileHandler(PATH_LOG, 'w')
file_handler.setLevel(logging.DEBUG)
file_format = "%(asctime)s %(levelname)8s [%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s"
file_formatter = logging.Formatter(fmt=file_format, datefmt='%H:%M:%S')
file_handler.setFormatter(file_formatter)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter(fmt="%(levelname)8s - %(message)s", datefmt='%H:%M:%S')
console_handler.setFormatter(console_formatter)

logger.addHandler(file_handler)
logger.addHandler(console_handler)