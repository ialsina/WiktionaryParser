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

#user_inp = input('Input word to search:\n>')
user_inp = 'table'

retrieved = parser.fetch(user_inp, 'english', wordclass=False)
# word_contents = parser.get_word_contents('english')
# tr = parser.parse_translations(wc, 0)
# wdo = parser.map_to_object(retrieved)

words = {}
for target in targets:
    logger.info("Fetching target: {}".format(target))
    retrieved = parser.fetch(target, wordclass=False)
    word = Word(retrieved, user_inp)
    words[target] = word
    translation = word.translation('russian')