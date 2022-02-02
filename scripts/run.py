import json
from wiktionaryparser.core import BaseParser, EnglishParser, SpanishParser
from deepdiff import DeepDiff
from typing import Dict, List
import mock
from urllib import parse
import os
from wiktionaryparser.logger import autolog

english_parser = EnglishParser()
spanish_parser = SpanishParser()

autolog('PARSING "HOUSE"', 3)
english_output = english_parser.fetch('house')

autolog('PARSING "CASA"', 3)
spanish_output = spanish_parser.fetch('casa')