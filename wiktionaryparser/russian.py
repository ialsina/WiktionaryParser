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


ENGLISH_RUSSIAN_DICT = {
    "noun"          : "существительное",
    "verb"          : "глагол",
    "adjective"     : "прилагательное",
    "adverb"        : "наречие",
    "determiner"    : "детерминанта",
    "article"       : "статья",
    "preposition"   : "предлог",
    "conjunction"   : "конъюнкция",
    "proper noun"   : "имя собственное",
    "letter"        : "письмо",
    "character"     : "персонаж",
    "phrase"        : "фраза",
    "proverb"       : "пословица",
    "idiom"         : "идиома",
    "symbol"        : "условное обозначение",
    "syllable"      : "слог",
    "numeral"       : "цифра",
    "initialism"    : "аббревиатуру",
    "interjection"  : "междометие", 
    "definitions"   : "определения",
    "pronoun"       : "местоимение",
    "translations"  : "перевод",
    "etymology"     : "этимология",
    "pronunciation" : "произношение",
}


class RussianParser(BaseParser):

    TRANSL = Translator(ENGLISH_RUSSIAN_DICT)
    LANG_PREFFIX = 'ru'

    def __init__(self):
        super().__init__()
        self.PARTS_OF_SPEECH = PARTS_OF_SPEECH
        self.RELATIONS = RELATIONS
        self.language = 'russian'
