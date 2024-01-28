from wiktionaryparser import WiktionaryParser, Word
from wiktionaryparser.logger import logger

targets = [
    'table',
    'hello',
    'hi',
    'the',
    'purple',
    'foamy'
]

words = []

parser = WiktionaryParser()

for target in targets:
    logger.info("Fetching target: {}".format(target))
    word = parser.fetch(target, language='english', wordclass=True)

    words.append(word)