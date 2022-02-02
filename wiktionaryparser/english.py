import re, requests
from wiktionaryparser.utils import WordData, Definition, RelatedWord
from bs4 import BeautifulSoup
from itertools import zip_longest
from copy import copy
from string import digits
from .core import BaseParser, Translator

PARTS_OF_SPEECH = [
    "noun", "verb", "adjective", "adverb", "determiner",
    "article", "preposition", "conjunction", "proper noun",
    "letter", "character", "phrase", "proverb", "idiom",
    "symbol", "syllable", "numeral", "initialism", "interjection",
    "definitions", "pronoun", "particle", "predicative", "participle",
    "suffix",
]

RELATIONS = [
    "synonyms", "antonyms", "hypernyms", "hyponyms",
    "meronyms", "holonyms", "troponyms", "related terms",
    "coordinate terms",
]


class EnglishParser(BaseParser):
    TRANSL = Translator({})
    LANG_PREFFIX = 'en'
    INTERFACE_LANGUAGE = 'English'

    def __init__(self):
        super().__init__()
        self.PARTS_OF_SPEECH = PARTS_OF_SPEECH
        self.RELATIONS = RELATIONS
        self.language = 'english'


