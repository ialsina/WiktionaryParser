from collections import defaultdict
from wiktionaryparser.dicts import PARTS_OF_SPEECH_DICT

class Word:
    def __init__(self, json_data, name=None):
        self._json_data = json_data
        self.name = name
        self.structure = [['{}'.format(PARTS_OF_SPEECH_DICT[elll.get('partOfSpeech')]) for elll in ell] for ell in
                          [el.get('definitions') for el in self._json_data]]
        self._pronunciation = [el.get('pronunciations').get('text') for el in self._json_data]
        self._etymology = [el.get('etimology') for el in self._json_data]
        self._meaning = [
            ['({}) {}'.format(PARTS_OF_SPEECH_DICT[elll.get('partOfSpeech')], '\n'.join(elll.get('text'))) for elll in
             ell] for ell in [el.get('definitions') for el in self._json_data]]
        self._meaning0 = [['{}'.format('\n'.join(elll.get('text'))) for elll in ell] for ell in
                          [el.get('definitions') for el in self._json_data]]
        self._languages = []
        self._translation_lst = defaultdict(dict)
        self._translation_txt = defaultdict(str)
        self.items = []
        self._parse_translations()

    def _parse_translations(self):

        for element in self._json_data: # usually only one element
            for definition in element.get('definitions'):
                part_of_speech = PARTS_OF_SPEECH_DICT[definition.get('partOfSpeech')]
                translations = definition.get('translations')
                for sense in translations:
                    sense_value = sense.get('sense')
                    languages = sense.get('translations')
                    self.items.append(list(languages.items()))
                    for lang, lang_value in languages.items():
                        if isinstance(lang_value, dict):
                            for descr, descr_value in lang_value.items():
                                descr_without_lang = descr.replace(lang + ' ', '').replace(' ' + lang, '')
                                lang_descr = lang + '-' + descr_without_lang
                                self._update_single_entry(lang_descr, part_of_speech, sense_value, descr_value)
                        else:
                            self._update_single_entry(lang, part_of_speech, sense_value, lang_value)
        for key in self._translation_txt:
            self._translation_txt[key] = self._translation_txt[key].replace('\n', '', 1) + '\n'
        self._languages = sorted(list(self._translation_txt.keys()))

    def _update_single_entry(self, key, part_of_speech, sense, value):
        self._translation_lst[key][self._dictionary_entry(part_of_speech, sense)] = self._force_comma_str(value)
        self._translation_txt[key] += '\n' + self._dictionary_entry(part_of_speech, sense, value)


    @classmethod
    def _dictionary_entry(cls, part_of_speech, sense, value=None):
        if value:
            return '({}) {}: {}'.format(part_of_speech, sense, cls._force_comma_str(value))
        else:
            return '({}) {}'.format(part_of_speech, sense)

    @classmethod
    def _force_comma_str(cls, value):
        if isinstance(value, list):
            return ', '.join(value)
        elif isinstance(value, str):
            return value
        else:
            raise TypeError('Wrong type')

    def pronunciation(self):
        raise NotImplemented

    def meaning(self):
        raise NotImplemented

    def translation(self, *args):
        if args == ():
            args = self._languages
        for arg in args:
            for lang in self._languages:
                if lang.startswith(arg):
                    print('\t>>', lang)
                    print(self._translation_txt.get(lang), flush=True)

    # Attempting to sort languages as in, e.g.
    # lang
    # lang-lang
    # lang-a
    # lang-z
    def translation0(self, *args):
        from copy import copy
        from itertools import zip_longest

        temp = []
        to_print = []

        if args == ():
            args = copy(self._languages)

        args = [el.lower() for el in args]
        langs = copy(self._languages)
        for arg in args:
            for lang in langs:
                if lang.startswith(arg):
                    temp.append((lang, self._translation_txt.get(lang)))
                    langs.remove(lang)

        temp = sorted(temp, lambda el: el[0])
        to_print = []

        cur_start = ''
        cur_chain = []
        chaining = True
        for ((key, var), (key_next, var_next)) in zip_longest(temp, temp[1:], fill=('', '')):
            pass

        for (key, val) in to_print:
            print('\t>> {}\n{}'.format(key, val))


class WordData(object):
    def __init__(self, etymology=None, definitions=None, pronunciations=None,
                 audio_links=None):
        self.etymology = etymology if etymology else ''
        self.definition_list = definitions
        self.pronunciations = pronunciations if pronunciations else []
        self.audio_links = audio_links if audio_links else []

    @property
    def definition_list(self):
        return self._definition_list

    @definition_list.setter
    def definition_list(self, definitions):
        if definitions is None:
            self._definition_list = []
            return
        elif not isinstance(definitions, list):
            raise TypeError('Invalid type for definition')
        else:
            for element in definitions:
                if not isinstance(element, Definition):
                    raise TypeError('Invalid type for definition')
            self._definition_list = definitions

    def to_json(self):
        return {
            'etymology': self.etymology,
            'definitions': [definition.to_json() for definition in self._definition_list],
            'pronunciations': {
                'text': self.pronunciations,
                'audio': self.audio_links
            }
        }


class Definition(object):
    def __init__(self, part_of_speech = None, text = None,
                 related_words = None, example_uses = None, translations = None):
        self.part_of_speech = part_of_speech if part_of_speech else ''
        self.text = text if text else ''
        self._related_words = related_words if related_words else []
        self.example_uses = example_uses if example_uses else []
        self._translations = translations if translations else []

    @property
    def related_words(self):
        return self._related_words

    @related_words.setter
    def related_words(self, related_words):
        if related_words is None:
            self._related_words = []
            return
        elif not isinstance(related_words, list):
            raise TypeError('Invalid type for relatedWord')
        else:
            for element in related_words:
                if not isinstance(element, RelatedWord):
                    raise TypeError('Invalid type for relatedWord')
            self._related_words = related_words

    @property
    def translations(self):
        return self._translations

    @translations.setter
    def translations(self, translations):
        self._translations = []
        if translations is None:
            return
        elif not isinstance(translations, list):
            raise TypeError('Invalid type for translation')
        else:
            for element in translations:
                translation_sense = element
                if not isinstance(element, TranslationSense):
                    if isinstance(element, tuple):
                        if len(element) == 2:
                            if isinstance(element[0], str) and isinstance(element[1], dict):
                                translation_sense = TranslationSense(element[0], element[1])
                            else:
                                raise TypeError('Invalid translation tuple formatting')
                        else:
                            raise TypeError('Invalid translation tuple formatting')
                    else:
                        raise TypeError('Invalid type for translation')
                self._translations.append(translation_sense)

    def to_json(self):
        return {
            'partOfSpeech': self.part_of_speech,
            'text': self.text,
            'relatedWords': [related_word.to_json() for related_word in self.related_words],
            'examples': self.example_uses,
            'translations': [sense.to_json() for sense in self.translations],
        }


class RelatedWord(object):
    def __init__(self, relationship_type=None, words=None):
        self.relationship_type = relationship_type if relationship_type else ''
        self.words = words if words else []

    def to_json(self):
        return {
            'relationshipType': self.relationship_type,
            'words': self.words
        }


class TranslationSense(object):
    def __init__(self, sense=None, translation_dict=None):
        self.sense = sense if sense else ''
        self.translations = translation_dict if translation_dict else {}

    def to_json(self):
        return {
            'sense': self.sense,
            'translations': self.translations
        }


class Debugger:
    KINDS = ["replace", "lock", "append", "stop"]
    DEFAULT_KIND = "replace"

    def __init__(self, default_kind = "replace", **kwargs):
        self._kinds = kwargs
        self._items = {}
        self._default_kind = default_kind

    def __setitem__(self, attr, val):
        assert attr in self.declared(), "Not declared"
        kind = self._kinds.get(attr)
        if kind == "replace":
            self._set(attr, val)
        elif kind == "lock":
            if attr not in self.initialized():
                self._set(attr, val)
        elif kind == "append":
            assert attr in self
            assert isinstance(self._get(attr), list)
            self._get(attr).append(val)
        elif kind == "stop":
            if attr in self.initialized():
                raise SystemExit("Stop requested by Debugger")

    def __getitem__(self, attr):
        assert attr in self.initialized(), "Not initialized"
        return self._get(attr)

    def __getattr__(self, attr):
        return self._get(attr)

    def __contains__(self, item):
        return item in self.delcared()

    def _set(self, attr, val):
        self._items.update(**{attr: val})

    def _get(self, attr):
        return self._items.get(attr)

    def declare(self, attr, kind=None):
        kind = kind or self.DEFAULT_KIND
        assert kind in self.KINDS, "Wrong kind"
        self._kinds.update(**{attr: kind})
        if kind == "append":
            self._items.update(**{attr: []})

    def print(self, attr, pretty=False, *args, **kwargs):
        output = self._get(attr)
        if pretty:
            output = output.prettify()
        print(output, *args, **kwargs)

    def declared(self):
        return list(self._kinds.keys())

    def initialized(self):
        return list(self._items.keys())
