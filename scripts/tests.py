from wiktionaryparser import WiktionaryParser, Word
from wiktionaryparser.logger import logger
import sys

parser = WiktionaryParser()

targets = [
    'table',
    'hello',
    'hi',
    'the',
    'purple',
    'foamy'
]

json_contents = {}
words = {}
translations_russian = {}
for target in targets:
    logger.info("Fetching target: {}".format(target))
    json_data = parser.fetch(target, return_word_class=False)
    word = Word(json_data, name=target)
    json_contents[target] = json_data
    words[target] = word
    translations_russian[target] = word.translation('russian')
