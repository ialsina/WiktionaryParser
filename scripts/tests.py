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

# user_inp = input('Input word to search:\n>')
# user_inp = 'table'

# retrieved = parser.fetch(user_inp, 'english', wordclass=False)
# word_contents = parser.get_word_contents('english')
# tr = parser.parse_translations(wc, 0)
# wdo = parser.map_to_object(retrieved)

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