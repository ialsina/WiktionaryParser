#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jul 10 08:35:54 2020

@author: ivan
"""

def invert_dict(original_dict):
    return {v: k for k, v in original_dict.items()}


class IdentityDict:
    def __getitem__(self,item):
        return item

    def get(self, item, *args, **kwargs):
        return item


class Translator:
    def __init__(self, source_lang, target_lang, dictionary):
        self.source = source_lang
        self.target = target_lang
        self.dictionary = dictionary

    def __call__(self, arg):
        if isinstance(arg, str):
            return self[arg]

        elif isinstance(arg, list):
            out = []
            for el in arg:
                out.append(self[el])
            return out

    def __getitem__(self, item):
        return self.dictionary.get(item)


PARTS_OF_SPEECH = [
    "noun", "verb", "adjective", "adverb", "determiner",
    "article", "preposition", "conjunction", "proper noun",
    "letter", "character", "phrase", "proverb", "idiom",
    "symbol", "syllable", "numeral", "initialism", "interjection",
    "definitions", "pronoun",
]

RELATIONS = [
    "synonyms", "antonyms", "hypernyms", "hyponyms",
    "meronyms", "holonyms", "troponyms", "related terms",
    "coordinate terms",
]

PARTS_OF_SPEECH_DICT = {
    "noun"          : "n",
    "verb"          : "v",
    "adjective"     : "adj",
    "adverb"        : "adv",
    "determiner"    : "det",
    "article"       : "art",
    "preposition"   : "prep",
    "conjunction"   : "conj",
    "proper noun"   : "pn",
    "letter"        : "let",
    "character"     : "chr",
    "phrase"        : "phr",
    "proverb"       : "prvb",
    "idiom"         : "idm",
    "symbol"        : "sym",
    "syllable"      : "syl",
    "numeral"       : "num",
    "initialism"    : "init",
    "interjection"  : "int",
    "definitions"   : "def",
    "pronoun"       : "pron",
}


PARTS_OF_SPEECH_INV = invert_dict(PARTS_OF_SPEECH_DICT)


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
    "prounuciation" : "произношение",
}


RUSSIAN_ENGLISH_DICT = invert_dict(ENGLISH_RUSSIAN_DICT)


IDENTITY = IdentityDict()

