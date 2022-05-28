from wiktionaryparser import WiktionaryParser, Word

parser = WiktionaryParser()

#user_inp = input('Input word to search:\n>')
user_inp = 'table'

retrieved = parser.fetch(user_inp, 'english', wordclass=False)
# word_contents = parser.get_word_contents('english')
# tr = parser.parse_translations(wc, 0)
# wdo = parser.map_to_object(retrieved)

word = Word(retrieved, user_inp)
translation = word.translation('russian')