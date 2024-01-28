import re, requests
from bs4 import BeautifulSoup
from itertools import zip_longest
from copy import copy
from string import digits

from wiktionaryparser.utils import WordData, Definition, RelatedWord, Debugger, Word
from wiktionaryparser.logger import autolog

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


class WiktionaryParser(object):
    def __init__(self, language="english"):
        self.url = "https://en.wiktionary.org/wiki/{}?printable=yes"
        self.soup = None
        self.session = requests.Session()
        self.session.mount("http://", requests.adapters.HTTPAdapter(max_retries=2))
        self.session.mount("https://", requests.adapters.HTTPAdapter(max_retries=2))
        self.language = language
        self.current_word = None
        self.PARTS_OF_SPEECH = copy(PARTS_OF_SPEECH)
        self.RELATIONS = copy(RELATIONS)
        self.INCLUDED_ITEMS = self.RELATIONS + self.PARTS_OF_SPEECH + ['etymology', 'pronunciation', 'translations']
        self.DEBUG = _new_debugger()

    def include_part_of_speech(self, part_of_speech):
        part_of_speech = part_of_speech.lower()
        if part_of_speech not in self.PARTS_OF_SPEECH:
            self.PARTS_OF_SPEECH.append(part_of_speech)
            self.INCLUDED_ITEMS.append(part_of_speech)

    def exclude_part_of_speech(self, part_of_speech):
        part_of_speech = part_of_speech.lower()
        self.PARTS_OF_SPEECH.remove(part_of_speech)
        self.INCLUDED_ITEMS.remove(part_of_speech)

    def include_relation(self, relation):
        relation = relation.lower()
        if relation not in self.RELATIONS:
            self.RELATIONS.append(relation)
            self.INCLUDED_ITEMS.append(relation)

    def exclude_relation(self, relation):
        relation = relation.lower()
        self.RELATIONS.remove(relation)
        self.INCLUDED_ITEMS.remove(relation)

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

        soup = self.soup
        contents = self.word_contents

        if content_type == 'etymologies':
            checklist = ['etymology']
        elif content_type == 'pronunciation':
            checklist = ['pronunciation']
        elif content_type == 'definitions':
            checklist = self.PARTS_OF_SPEECH
            if self.language == 'chinese':
                checklist += self.current_word
        elif content_type == 'related':
            checklist = self.RELATIONS
        elif content_type == 'translations':
            checklist = ['translations']
        else:
            return None
        id_list = []
        if len(contents) == 0:
            return [('1', x.title(), x) for x in checklist if self.soup.find('span', {'id': x.title()})]
        for content_tag in contents:
            content_index = content_tag.find_previous().text
            text_to_check = self.remove_digits(content_tag.text).strip().lower()
            if text_to_check in checklist:
                content_id = content_tag.parent['href'].replace('#', '')
                id_list.append((content_index, content_id, text_to_check))
        autolog('IN: {} | OUT: {}'.format(content_type, id_list), 0)
        return id_list

    def get_word_contents(self, language):
        contents = self.soup.find_all('span', {'class': 'toctext'})
        word_contents = []
        start_index = None
        for content in contents:
            if content.text.lower() == language:
                start_index = content.find_previous().text + '.'
        if len(contents) > 0 and start_index is None:
            autolog(contents, 2)
            return []
        for content in contents:
            index = content.find_previous().text
            content_text = self.remove_digits(content.text.lower())
            if index.startswith(start_index) and content_text in self.INCLUDED_ITEMS:
                word_contents.append(content)
        autolog('CHECK2')
        self.word_contents = word_contents
        self.DEBUG['word_contents'] = word_contents
        autolog(word_contents, 0)
        return word_contents

    def get_word_data(self, language):
        word_data = {
            'examples': self.parse_examples(),
            'definitions': self.parse_definitions(),
            'etymologies': self.parse_etymologies(),
            'related': self.parse_related_words(),
            'pronunciations': self.parse_pronunciations(),
            'translations': self.parse_translations(),
        }
        self.DEBUG['word_data0'] = word_data
        json_obj_list = self.map_to_object(word_data)
        self.DEBUG['get_word_data'] = json_obj_list
        self.DEBUG['word_data'] = json_obj_list
        autolog('OUT: {}'.format('See DEBUG["get_word_data"]'), 2)
        json_obj_list = self.map_to_object(word_data)
        return json_obj_list

    def parse_pronunciations(self):
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
        etymology_id_list = self.get_id_list('etymologies')
        etymology_list = []
        etymology_tag = None
        for etymology_index, etymology_id, _ in etymology_id_list:
            etymology_text = ''
            span_tag = self.soup.find_all('span', {'id': etymology_id})[0]
            next_tag = span_tag.parent.find_next_sibling()
            while next_tag and next_tag.name not in ['h3', 'h4', 'div', 'h5']:
                etymology_tag = next_tag
                next_tag = next_tag.find_next_sibling()
                if etymology_tag.name == 'p':
                    etymology_text += etymology_tag.text
                else:
                    for list_tag in etymology_tag.find_all('li'):
                        etymology_text += list_tag.text + '\n'
            etymology_list.append((etymology_index, etymology_text))
        return etymology_list

    def parse_related_words(self):
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

    def parse_translations(self):
        """Returns a structure of the kind:
        [
            ( index1, [
                        sense 1.1, {lang1: transl1, lang2: defs2, ... },
                        sense 1.2, {lang1: transl1, lang2: defs2, ... },
                        ...
                      ]
            ),
            ( index2, ...),
            ...
        ]
            """
        translations_id_list = self.get_id_list('translations')
        translations_list = []
        self.DEBUG['translations_id_list'] = translations_id_list
        for translations_index, translations_id, _ in translations_id_list:
            cur_translation_list = []
            span_tag = self.soup.find_all('span', {'id': translations_id})[0]
            self.DEBUG['transl1'] = span_tag
            transl_tag = span_tag.parent.find_next_sibling()
            cur_transl_senses = _get_senses(transl_tag)
            self.DEBUG['transl_tag'] = transl_tag
            self.DEBUG['last_transl_tag'] = cur_transl_senses[-1]
            # If translations are somewhere else, go look for them
            if len(cur_transl_senses) == 1 and '/translations' in cur_transl_senses[0][1].text:
                span_tag = _second_lookup(self.url, cur_transl_senses)
                if self.DEBUG.get('transl2') is None: self.DEBUG['transl2'] = span_tag
                cur_transl_senses = _get_senses(span_tag.parent.find_next_sibling().find_next_sibling())
            for (sense, sense_tag) in cur_transl_senses:
                cur_translation_list.append((sense, _extract_languages(sense_tag)))
                self.DEBUG['extract_languages'] = cur_translation_list
            self.DEBUG['cur_transl_list'] = cur_translation_list

            translations_list.append((translations_index, cur_translation_list))
        autolog('translations_list: {}'.format(translations_list), 0)
        self.DEBUG['translations_list'] = translations_list
        self.DEBUG['parse_translations'] = translations_list
        return translations_list

    def map_to_object(self, word_data):
        self.DEBUG['map_to_object_input'] = word_data
        json_obj_list = []
        if not word_data['etymologies']:
            word_data['etymologies'] = [('', '')]

        # Loop over etimologies
        for (current_etymology, next_etymology) in zip_longest(word_data['etymologies'], word_data['etymologies'][1:], fillvalue=('999', '')):
            data_obj = WordData()
            data_obj.etymology = current_etymology[1]

            # Loop over pronunciations
            # Check if:
            #   1. Pronunciation is at the same level of etymology(ies)
            #   2. Proununciation index "is sorted" after current etymology index
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
                    autolog('\n>> {} {}'.format(definition_index,definition_text), 0)
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
                    for translations_index, translations_dict in word_data['translations']:
                        if definition_index <= translations_index < next_definition_index:
                            def_obj.translations = translations_dict
                            autolog('COND 1: {} {}'.format(translations_index, definition_index), 0)
                    data_obj.definition_list.append(def_obj)
            self.DEBUG['data_obj'] = data_obj
            json_obj_list.append(data_obj.to_json())

        self.DEBUG['map_to_object'] = json_obj_list
        self.DEBUG['json_obj_list'] = json_obj_list
        autolog('OUT: See DEBUG["map_to_object"]', 0)

        return json_obj_list

    def fetch(self, word, language=None, old_id=None, wordclass=True):
        language = self.language if not language else language
        response = self.session.get(self.url.format(word), params={'oldid': old_id})
        self.soup = BeautifulSoup(response.text.replace('>\n<', '><'), 'html.parser')
        self.current_word = word
        self.clean_html()
        self.get_word_contents(language)
        word_data = self.get_word_data(language)
        if not wordclass:
            return word_data
        else:
            return Word(word_data, self.current_word)


def _is_subheading(child, parent):
    child_headings = child.split(".")
    parent_headings = parent.split(".")
    if len(child_headings) <= len(parent_headings):
        return False
    for child_heading, parent_heading in zip(child_headings, parent_headings):
        if child_heading != parent_heading:
            return False
    return True


def _second_lookup(url, url_preffix, transl_senses):
    autolog(transl_senses, 2)
    url2 = transl_senses[0][1].find('a').get('href').replace('/wiki/', '')
    session2 = requests.Session()
    session2.mount("http://", requests.adapters.HTTPAdapter(max_retries=2))
    session2.mount("https://", requests.adapters.HTTPAdapter(max_retries=2))
    response = session2.get(url.format(url2))
    soup2 = BeautifulSoup(response.text, 'html.parser')
    return soup2.find('span', {'id': url2.split('#')[1]})


def _get_senses(transl_tag):
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
        except:
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


def _extract_language_item(lang_tag):
    unwanted_classes = ['tpos']
    enclose_classes = ['gender']

    # Extract unwanted classes. Enclose genders
    for tag in lang_tag.find_all(True, {'class': unwanted_classes}):
        tag.extract()
    for tag in lang_tag.find_all(True, {'class': enclose_classes}):
        tag.replace_with('[' + tag.text + ']')

    # Take text, and separate: lang & translation (by colon)
    text = lang_tag.text
    try:
        key, items_text = text.split(':', 1)
        text = [el.strip() for el in text]
        autolog(f'KEY: {key}\n\tITEMS_TEXT: {items_text}', 2)
    except:
        print(text)
        raise Exception("Impossible to extract language")

    # Separate different items (by commas)
    # Also, replace '[[a|b]]' for 'b' (gender notation)
    items_list = items_text.split(', ')
    for i in range(len(items_list)):
        item = items_list[i]
        if '[[' in item and ']]' in item and '|' in item:
            items_list[i] = item.split('|')[1].replace(']]', '')

    # If all ',()' chars are in text, go through list so as to ignore , between ()
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


def _extract_languages(sense_tag):
    lang_tags = sense_tag.find_all('li')
    lang_dict = {}
    for lang_tag in lang_tags:
        if not lang_tag.find_all('dl'):
            # There are no dialects (subitems in a language)
            lang_dict = dict(lang_dict, **_extract_language_item(lang_tag))
        else:
            # There are dialects
            lang = lang_tag.text.split(':')[0]
            descriptions_dict = {}

            temp = copy(lang_tag)
            temp.find('dl').extract()

            if temp.text.replace('\n', '').split(':')[1] != '':
                # There is still a main entry
                autolog('SENDING {}'.format(temp), 2)
                descriptions_dict = dict(descriptions_dict, **_extract_language_item(temp))

            for descr in lang_tag.find_all('dd'):
                if not descr.find_all('dl'):
                    autolog('LANG: {}, NOT dl: {}'.format(lang, descr), 0)
                    descriptions_dict = dict(descriptions_dict, **_extract_language_item(descr))
                else:
                    autolog('SPECIAL CASE. LANG: {}, YES dl: {}'.format(lang, descr), 2)
                    for descr2 in descr.find_all('dl'):
                        descriptions_dict = dict(descriptions_dict, **_extract_language_item(descr2))
                        descr2.extract()
                    descriptions_dict = dict(descriptions_dict, **_extract_language_item(descr))
            lang_dict[lang.lower()] = descriptions_dict
    return lang_dict


def _new_debugger():
    return Debugger(
        word_contents='stop',
        cur_transl_list='lock',
        extract_languages = 'replace',
        transl_tag='replace',
        cur_transl_tag='replace',
        last_transl_tag = 'replace',
        translations_list='replace',
        parse_translations='lock',
        map_to_object_input = 'replace',
        map_to_object = 'replace',
        json_obj_list = 'replace',
        word_data0 = 'replace',
        word_data = 'replace',
        get_word_data = 'replace',
        translations_id_list = 'lock',
        transl1 = 'lock',
        data_obj = 'lock',
    )
