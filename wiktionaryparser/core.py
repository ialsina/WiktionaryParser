import re, requests
from wiktionaryparser.utils import WordData, Definition, RelatedWord
from bs4 import BeautifulSoup
from itertools import zip_longest
from copy import copy
from string import digits
from abc import ABC, abstractmethod
from .logger import autolog

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


def is_subheading(child, parent):
    child_headings = child.split(".")
    parent_headings = parent.split(".")
    if len(child_headings) <= len(parent_headings):
        return False
    for child_heading, parent_heading in zip(child_headings, parent_headings):
        if child_heading != parent_heading:
            return False
    return True


class Translator:

    def __init__(self, glossary, language=None):
        assert isinstance(glossary, dict)
        self._glossary = glossary
        self.language = language

    def __call__(self, val, default=None):

        if isinstance(val, str):
            return self._translate(val, default)

        elif isinstance(val, list) or isinstance(val, tuple):
            return [self._translate(el, default) for el in val]

        else:
            raise TypeError

    def __getitem__(self, key):
        output = self._glossary.get(key)
        return output

    def __setitem__(self, key, val):
        self._glossary[key] = val

    def _translate(self, query, default=None):
        query = query.lower()
        result = self._glossary.get(query)
        if result is None:
            result = {v: k for k, v in self._glossary.items()}.get(query)
            if result is None:
                result = query if default is None else default
        return result

    def keys(self):
        return self._glossary.keys()

    def values(self):
        return self._glossary.values()

    def items(self):
        return self._glossary.items()

    def all(self):
        return set(list(self.keys()) + list(self.values()))


class BaseParser(ABC):

    def __init__(self):
        self.url = "https://{lang_pref}.wiktionary.org/wiki/{query}?printable=yes"
        self.soup = None
        self.soup2 = None
        self.session = requests.Session()
        self.session.mount("http://", requests.adapters.HTTPAdapter(max_retries=2))
        self.session.mount("https://", requests.adapters.HTTPAdapter(max_retries=2))
        self.language = None
        self.current_word = None
        self.word_data = None
        self.word_contents = None
        self.get_translations = None
        self.PARTS_OF_SPEECH = []
        self.RELATIONS = []
        self._DEBUG = {}

    # @property
    # @abstractmethod
    # def PARTS_OF_SPEECH(self):
    #    pass
    #
    #    #@property
    #    #@abstractmethod
    #    #def RELATIONS(self):
    #    pass

    @property
    @abstractmethod
    def TRANSL(self):
        pass

    @property
    @abstractmethod
    def LANG_PREFFIX(self):
        pass

    @property
    def INCLUDED_ITEMS(self):
        extra = ['etymology', 'pronunciation']
        if self.get_translations:
            extra.append('translations')
        return self.TRANSL(self.RELATIONS + self.PARTS_OF_SPEECH + extra)

    def include_part_of_speech(self, part_of_speech):
        part_of_speech = part_of_speech.lower()
        if part_of_speech not in self.PARTS_OF_SPEECH:
            self.PARTS_OF_SPEECH.append(part_of_speech)

    def exclude_part_of_speech(self, part_of_speech):
        part_of_speech = part_of_speech.lower()
        self.PARTS_OF_SPEECH.remove(part_of_speech)

    def include_relation(self, relation):
        relation = relation.lower()
        if relation not in self.RELATIONS:
            self.RELATIONS.append(relation)

    def exclude_relation(self, relation):
        relation = relation.lower()
        self.RELATIONS.remove(relation)

    def set_default_language(self, language=None):
        if language is not None:
            self.language = language.lower()

    def get_default_language(self):
        return self.language

    def clean_html(self):
        unwanted_classes = ['sister-wikipedia', 'thumb', 'reference', 'cited-source']
        for tag in self.soup.find_all(True, {'class': unwanted_classes}):
            tag.extract()

    def remove_digits(self, string):
        return string.translate(str.maketrans('', '', digits)).strip()

    def count_digits(self, string):
        return len(list(filter(str.isdigit, string)))

    def get_id_list(self, content_type):
        """Searches in word contents, with the aim of finding the section id of those
        sections whose content type matches the requested one.

        INPUT:
            content_type (str)
        OUTPUT:
            a list of tuples with the following format:
                (index, id, text_that_matched_criteria)
            Example 1: content_type: 'pronunciation'
                [('1.1', 'Pronunciation', 'pronunciation')]

            Example 2: content_type: 'definitions'
                [('1.2.1', 'Noun', 'noun'),
                ('1.2.3', 'Verb', 'verb'),
                ('1.3.1', 'Noun_2', 'noun')]
        """

        word_contents = self.word_contents

        if content_type == 'etymologies':
            checklist = self.TRANSL(['etymology'])
        elif content_type == 'pronunciation':
            checklist = self.TRANSL(['pronunciation'])
        elif content_type == 'definitions':
            checklist = self.TRANSL(self.PARTS_OF_SPEECH)
            if self.language == 'chinese':
                checklist += self.current_word
        elif content_type == 'related':
            checklist = self.TRANSL(self.RELATIONS)
        elif content_type == 'translations':
            checklist = self.TRANSL(['translations'])
        else:
            return None
        id_list = []
        if len(word_contents) == 0:
            return [('1', x.title(), x) for x in checklist if self.soup.find('span', {'id': x.title()})]
        for content_tag in word_contents:
            content_index = content_tag.find_previous().text
            text_to_check = self.remove_digits(content_tag.text).strip().lower()
            if text_to_check in checklist:
                content_id = content_tag.parent['href'].replace('#', '')
                id_list.append((content_index, content_id, text_to_check))
        return id_list

    def parse_pronunciations(self):
        word_contents = self.word_contents
        pronunciation_id_list = self.get_id_list('pronunciation')
        pronunciation_list = []
        audio_links = []
        pronunciation_div_classes = ['mw-collapsible', 'vsSwitcher']
        for pronunciation_index, pronunciation_id, _ in pronunciation_id_list:
            pronunciation_text = []
            span_tag = self.soup.find_all('span', {'id': pronunciation_id})[0]
            list_tag = span_tag.parent
            while list_tag.name != 'ul':
                list_tag = list_tag.find_next_sibling()
                if list_tag.name == 'p':
                    pronunciation_text.append(list_tag.text)
                    break
                if list_tag.name == 'div' and any(_ in pronunciation_div_classes for _ in list_tag['class']):
                    break
            for super_tag in list_tag.find_all('sup'):
                super_tag.clear()
            for list_element in list_tag.find_all('li'):
                for audio_tag in list_element.find_all('div', {'class': 'mediaContainer'}):
                    audio_links.append(audio_tag.find('source')['src'])
                    audio_tag.extract()
                for nested_list_element in list_element.find_all('ul'):
                    nested_list_element.extract()
                if list_element.text and not list_element.find('table', {'class': 'audiotable'}):
                    pronunciation_text.append(list_element.text.strip())
            pronunciation_list.append((pronunciation_index, pronunciation_text, audio_links))
        return pronunciation_list

    def parse_definitions(self):
        word_contents = self.word_contents
        definition_id_list = self.get_id_list('definitions')
        definition_list = []
        definition_tag = None
        for def_index, def_id, def_type in definition_id_list:
            definition_text = []
            span_tag = self.soup.find_all('span', {'id': def_id})[0]
            table = span_tag.parent.find_next_sibling()
            while table and table.name not in ['h3', 'h4', 'h5']:
                definition_tag = table
                table = table.find_next_sibling()
                if definition_tag.name == 'p':
                    if definition_tag.text.strip():
                        definition_text.append(definition_tag.text.strip())
                if definition_tag.name in ['ol', 'ul']:
                    for element in definition_tag.find_all('li', recursive=False):
                        if element.text:
                            definition_text.append(element.text.strip())
            if def_type == 'definitions':
                def_type = ''
            definition_list.append((def_index, definition_text, def_type))
        return definition_list

    def parse_examples(self):
        word_contents = self.word_contents
        definition_id_list = self.get_id_list('definitions')
        example_list = []
        for def_index, def_id, def_type in definition_id_list:
            span_tag = self.soup.find_all('span', {'id': def_id})[0]
            table = span_tag.parent
            while table.name != 'ol':
                table = table.find_next_sibling()
            examples = []
            while table and table.name == 'ol':
                for element in table.find_all('dd'):
                    example_text = re.sub(r'\([^)]*\)', '', element.text.strip())
                    if example_text:
                        examples.append(example_text)
                    element.clear()
                example_list.append((def_index, examples, def_type))
                for quot_list in table.find_all(['ul', 'ol']):
                    quot_list.clear()
                table = table.find_next_sibling()
        return example_list

    def parse_etymologies(self):
        word_contents = self.word_contents
        etymology_id_list = self.get_id_list('etymologies')
        autolog(etymology_id_list)
        etymology_list = []
        etymology_tag = None
        for etymology_index, etymology_id, _ in etymology_id_list:
            etymology_text = ''
            span_tag = self.soup.find_all('span', {'id': etymology_id})[0]
            next_tag = span_tag.parent.find_next_sibling()
            autolog('next_tag = {}'.format(next_tag))
            while next_tag and next_tag.name not in ['h3', 'h4', 'div', 'h5']:
                autolog('next_tag: VALID')
                etymology_tag = next_tag
                next_tag = next_tag.find_next_sibling()
                autolog('next_tag = {}'.format(next_tag))
                if etymology_tag.name == 'p':
                    etymology_text += etymology_tag.text
                else:
                    for list_tag in etymology_tag.find_all('li'):
                        etymology_text += list_tag.text + '\n'
            etymology_list.append((etymology_index, etymology_text))
        autolog(etymology_list)
        return etymology_list

    def parse_related_words(self):
        word_contents = self.word_contents
        relation_id_list = self.get_id_list('related')
        related_words_list = []
        for related_index, related_id, relation_type in relation_id_list:
            words = []
            span_tag = self.soup.find_all('span', {'id': related_id})[0]
            parent_tag = span_tag.parent
            while parent_tag and not parent_tag.find_all('li'):
                parent_tag = parent_tag.find_next_sibling()
            if parent_tag:
                for list_tag in parent_tag.find_all('li'):
                    words.append(list_tag.text)
            related_words_list.append((related_index, words, relation_type))
        return related_words_list

    def _extract_languages(self, sense_tag):
        lang_tags = sense_tag.find_all('li')
        lang_dict = {}
        for lang_tag in lang_tags:
            if not lang_tag.find_all('dl'):
                # There are no dialects (i.e. subitems in a language)
                lang_dict = dict(lang_dict, **self._extract_language_item(lang_tag))
            else:
                # There are dialects
                lang = lang_tag.text.split(':')[0]
                descriptions_dict = {}

                temp = copy(lang_tag)
                temp.find('dl').extract()

                if temp.text.replace('\n', '').split(':')[1] != '':
                    # There is still a main entry
                    descriptions_dict = dict(descriptions_dict, **self._extract_language_item(temp))

                for description in lang_tag.find_all('dd'):
                    if not description.find_all('dl'):
                        descriptions_dict = dict(descriptions_dict, **self._extract_language_item(description))
                    else:
                        for description2 in description.find_all('dl'):
                            descriptions_dict = dict(descriptions_dict, **self._extract_language_item(description2))
                            description2.extract()
                        descriptions_dict = dict(descriptions_dict, **self._extract_language_item(description))
                lang_dict[lang.lower()] = descriptions_dict

        return lang_dict

    def _extract_language_item(self, lang_tag):
        unwanted_classes = ['tpos']
        enclose_classes = ['gender']

        # Extract unwanted classes. Enclose genders between square brackets
        for tag in lang_tag.find_all(True, {'class': unwanted_classes}):
            tag.extract()
        for tag in lang_tag.find_all(True, {'class': enclose_classes}):
            tag.replace_with("[{}]".format(tag.text))

        # Take text, and separate: lang & translation (by colon)
        text = lang_tag.text
        try:
            key, items_text = text.split(':', 1)
            text = [el.strip() for el in text]
        except Exception:
            print(text)
            raise Exception("Impossible to extract language")

        # Separate different items (by commas)
        # Also, replace '[[a|b]]' by 'b' (gender notation)
        items_list = items_text.split(', ')
        for i in range(len(items_list)):
            item = items_list[i]
            if '[[' in item and ']]' in item and '|' in item:
                items_list[i] = item.split('|')[1].replace(']]', '')

        # If all ',()' chars are in text, go through list so as to ignore any ',' between '(' and ')'
        if ',' in items_text and '(' in items_text and ')' in items_text:
            items_new = []
            cur_chain = []
            connecting = False
            counts = [0, 0]
            for el in items_list:
                counts[0] += el.count('(')
                counts[1] += el.count(')')
                cur_chain.append(el)
                if counts[0] == counts[1]:
                    items_new.append(', '.join(cur_chain))
                    cur_chain = []

            items_list = items_new

        # Return a dict whose value is the list or its only element
        return {key.lower(): items_list if len(items_list) > 1 else items_list[0]}

    def _extract_senses(self, transl_tag):
        """Builds and returns a dictionary of translation siblings (bs4.element.Tag),
        i.e. one for each of the senses of a word.
        Output format:
            {
                (sense1, bs4.element.Tag with all the languages),
                (sense2, bs4.element.Tag with all the languages),
            }
        """

        sense_tag = transl_tag

        senses = []

        while True:
            # Check if the table of senses is over
            if sense_tag is None:
                break
            try:
                sense_tag_name = sense_tag.name
            except Exception:
                break
            if sense_tag_name in ['h3', 'h4', 'h5']:
                break

            # get the sense name
            sense_header = sense_tag.find('div')
            if sense_header is None:
                sense = ''
            else:
                sense = sense_header.text

            # add to dictionary
            senses.append((sense, sense_tag))
            sense_tag = sense_tag.find_next_sibling()

        return senses

    def parse_translations(self):
        """Returns a structure of the kind:
        [
            (
              index1, [
                        sense 1.1, {lang1: transl1, lang2: defs2, ... },
                        sense 1.2, {lang1: transl1, lang2: defs2, ... },
                        ...
                      ]
            ),
            ( index2, [...] ),
            ...
        ]
            """
        word_contents = self.word_contents
        translations_id_list = self.get_id_list('translations')
        translations_list = []

        for translations_index, translations_id, _ in translations_id_list:

            cur_translation_list = []

            span_tag = self.soup.find_all('span', {'id': translations_id})[0]
            cur_transl_senses = self._extract_senses(span_tag.parent.find_next_sibling())

            # If translations are somewhere else, go look for them
            if len(cur_transl_senses) == 1 and '/translations' in cur_transl_senses[0][1].text:
                url2 = cur_transl_senses[0][1].find('a').get('href').replace('/wiki/', '')

                session2 = requests.Session()
                session2.mount("http://", requests.adapters.HTTPAdapter(max_retries=2))
                session2.mount("https://", requests.adapters.HTTPAdapter(max_retries=2))
                response = session2.get(self.url.format(self.url_preffix, url2))
                soup2 = BeautifulSoup(response.text, 'html.parser')
                span_tag = soup2.find('span', {'id': url2.split('#')[1]})
                self.soup2 = soup2

                cur_transl_senses = self._extract_senses(span_tag.parent.find_next_sibling().find_next_sibling())

            for (sense, sense_tag) in cur_transl_senses:
                cur_translation_list.append((sense, self._extract_languages(sense_tag)))

            translations_list.append((translations_index, cur_translation_list))

        return translations_list

    def get_word_contents(self, language):
        """Returns list of bs4.element.Tag whose text is in the recognized terms
        and in the appropriate language
        """

        contents = self.soup.find_all('span', {'class': 'toctext'})
        word_contents = []
        start_index = None

        # First find language to define index
        for content in contents:
            if content.text.lower() == language:
                start_index = content.find_previous().text + '.'
        if len(contents) != 0 and start_index is None:
            return []

        # Pick contents with appropriate index (thus language)
        for content in contents:
            index = content.find_previous().text
            content_text = self.remove_digits(content.text.lower())
            autolog("content_text: {}".format(content_text))
            #if index.startswith(start_index) and content_text in self.INCLUDED_ITEMS:
            if index.startswith(start_index) and any(el in content_text for el in self.INCLUDED_ITEMS):
                autolog("content_text----VALID")
                word_contents.append(content)

        self.word_contents = word_contents
        return word_contents

    def get_word_data(self):
        word_data = {
            'examples': self.parse_examples(),
            'definitions': self.parse_definitions(),
            'etymologies': self.parse_etymologies(),
            'related': self.parse_related_words(),
            'pronunciations': self.parse_pronunciations(),
        }

        if self.get_translations:
            word_data['translations'] = self.parse_translations()

        self.word_data = word_data
        return word_data

    def map_to_object(self, json=False):
        obj_list = []
        word_data = self.word_data

        if not word_data['etymologies']:
            word_data['etymologies'] = [('', '')]

        # Loop over etymologies
        for (current_etymology, next_etymology) in zip_longest(word_data['etymologies'], word_data['etymologies'][1:], fillvalue=('999', '')):
            data_obj = WordData()
            data_obj.etymology = current_etymology[1]

            # Loop over pronunciations
            # Check if:
            #   1. Pronunciation is at the same level of etymology(ies)
            #   2. Pronunciation index "is sorted" after current etymology index
            #      and before next etymology index (string comparison)

            for pronunciation_index, pronunciation_text, audio_links in word_data['pronunciations']:
                if (self.count_digits(current_etymology[0]) == self.count_digits(pronunciation_index)) or (current_etymology[0] <= pronunciation_index < next_etymology[0]):
                    data_obj.pronunciations = pronunciation_text
                    data_obj.audio_links = audio_links

            # Loop over definitions
            # Check if definition index "sorts" after current etymology index
            # and before next etymology index (string comparison)
            # If so, loop over examples, related and translations, and for each one,
            # pick the ones whose index starts like the definition index

            for (current_definition, next_definition) in zip_longest(word_data['definitions'], word_data['definitions'][1:], fillvalue=('999', '', '')):
                definition_index, definition_text, definition_type = current_definition
                next_definition_index, _, _ = next_definition

                if current_etymology[0] <= definition_index < next_etymology[0]:
                    def_obj = Definition()
                    def_obj.text = definition_text
                    def_obj.part_of_speech = definition_type
                    for example_index, examples, _ in word_data['examples']:
                        if example_index.startswith(definition_index):
                            def_obj.example_uses = examples
                    for related_word_index, related_words, relation_type in word_data['related']:
                        if related_word_index.startswith(definition_index):
                            def_obj.related_words.append(RelatedWord(relation_type, related_words))
                    found = False
                    if self.get_translations:
                        for translations_index, translations_dict in word_data['translations']:
                            if definition_index <= translations_index < next_definition_index:
                                def_obj.translations = translations_dict

                    data_obj.definition_list.append(def_obj)

            obj_list.append(data_obj)

        if json:
            obj_list = [el.to_json() for el in obj_list]

        return obj_list

    def fetch(self, word, language=None, old_id=None, json=False, get_translations=True):
        language = self.language if not language else language
        response = self.session.get(self.url.format(lang_pref=self.LANG_PREFFIX, query=word), params={'oldid': old_id})
        #self._DEBUG['request'] = requests.Request('GET', self.url.format(lang_pref=self.LANG_PREFFIX, query=word), params={'oldid': old_id})
        #self._DEBUG['prequest'] = self.session.prepare_request(self._DEBUG['request'])
        self.soup = BeautifulSoup(response.text.replace('>\n<', '><'), 'html.parser')
        self.soup2 = None
        self.current_word = word
        self.clean_html()
        self.get_word_contents(language.lower())
        self.get_word_data()
        return self.map_to_object(json=json)
