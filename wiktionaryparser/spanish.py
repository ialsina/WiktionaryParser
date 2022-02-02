import re, requests
from wiktionaryparser.utils import WordData, Definition, RelatedWord
from bs4 import BeautifulSoup
from itertools import zip_longest
from copy import copy
from string import digits
from .core import BaseParser, Translator
from .logger import autolog

PARTS_OF_SPEECH = [
    "noun", "verb", "verbal form", "adjective", "adverb", "determiner",
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


ENGLISH_SPANISH = {
    "noun"          : "sustantivo",
    "verb"          : "verbo",
    "verbal form"   : "forma verbal",
    "adjective"     : "adjetivo",
    "adverb"        : "adverbio",
    "determiner"    : "determinante",
    "article"       : "artículo",
    "preposition"   : "preposición",
    "conjunction"   : "conjunción",
    "proper noun"   : "nombre propio",
    "letter"        : "letra",
    "character"     : "carácter",
    "phrase"        : "frase",
    "proverb"       : "refrán",
    "idiom"         : "locución",
    "symbol"        : "símbolo",
    "syllable"      : "sílaba",
    "numeral"       : "numeral",
    "initialism"    : "inicialismo",
    "interjection"  : "interjección",
    "definitions"   : "definiciones",
    "pronoun"       : "prononbre",
    "translations"  : "traducciones",
    "etymology"     : "etimología",
    "pronunciation" : "pronunciación",
    "examples"      : "ejemplos",
    'synonyms'      : "sinónimos",
    'particle' : "partícula",
     'antonyms': "antónimos",
     'hypernyms': "hiperónimos",
     'hyponyms': "hipónimos",
     'meronyms': "merónimos",
     'holonyms': "holónimos",
     'troponyms': "tropónimos",
     'related terms': "relacionados",
     'coordinate terms': "coordinados"
}


class SpanishParser(BaseParser):

    TRANSL = Translator(ENGLISH_SPANISH)
    LANG_PREFFIX = 'es'

    def __init__(self):
        super().__init__()
        self.PARTS_OF_SPEECH = PARTS_OF_SPEECH
        self.RELATIONS = RELATIONS
        self.language = 'español'

    def parse_etymologies(self):
        word_contents = self.word_contents
        etymology_id_list = self.get_id_list('etymologies')
        autolog(etymology_id_list)
        etymology_list = []
        self._DEBUG['et'] = []
        etymology_tag = None
        for etymology_index, etymology_id, _ in etymology_id_list:
            etymology_text = ''
            span_tag = self.soup.find_all('span', {'id': etymology_id})[0]
            self._DEBUG['et'].append(span_tag)
            next_tag = span_tag.find_next_sibling()
            autolog('next_tag = {}'.format(next_tag))
            while next_tag and next_tag.name not in ['h3', 'h4', 'div', 'h5']:
                etymology_tag = next_tag
                next_tag = next_tag.find_next_sibling()
                if etymology_tag.name == 'p':
                    etymology_text += etymology_tag.text
                else:
                    for list_tag in etymology_tag.find_all('li'):
                        etymology_text += list_tag.text + '\n'
            etymology_list.append((etymology_index, etymology_text))
        autolog(etymology_list)
        return etymology_list
