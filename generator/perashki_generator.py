import re
import argparse
import unittest
from collections import Counter, defaultdict
import random
from os import listdir
from os.path import isfile, join
import pickle
import itertools

from phonetics.phonetics import Phonetics

from django.conf import settings

MAX_RANDOM_ITER = 100


def tokenize(line):
    return [token.lower() for token in re.findall(r"[^\W\d]+|[^\w\s]+|\s+|\d+", line, re.LOCALE & re.UNICODE)]


def tokenize_without_punctuation(line):
    for token in re.findall(r"[а-яА-Я][а-яА-Я\-\s]*", line, re.LOCALE & re.UNICODE):
        yield itertools.chain(*([t.split('-') for t in token.strip().lower().split()]))


def output_tokens(input_stream, args):
    line = input_stream.readline()

    with open('output.txt', 'w', encoding='utf-8') as output_stream:
        for token in tokenize(line.strip()):
            print(token, file=output_stream)


class MarkovChainsGenerator:
    def __init__(self, depth):
        self.depth = depth
        self.frequencies = defaultdict(Counter)
        self.number_of_syllables = { True : 9, False : 8 }
        self.russian_vowels = "ёуеыаоэяию"                

    def calculate_probabilities(self, token_generator):
        current_tokens = []
        for index, token in enumerate(token_generator):
            for start in range(len(current_tokens) + 1):
                chain = tuple(current_tokens[start:])
                if (len(chain) == 0 and index != 0) or not self._is_chain_legal(list(chain) + [token]):
                    continue
                self.frequencies[chain][token] += 1

            if len(current_tokens) == self.depth:
                current_tokens.pop(0)
            current_tokens.append(token)
            
    def get_probabilities_table(self):
        probabilities_table = {}

        for chain, token_counter in self.frequencies.items():
            size = sum(token_counter.values())
            probabilities_table[' '.join(chain)] = [(token, freq / size)
                                                    for token, freq
                                                    in sorted(token_counter.items())]
        return probabilities_table

    def _make_random_token(self, chain=tuple()):
        token_counter = self.frequencies[chain]

        if not token_counter:
            return None

        size = sum(token_counter.values())
        random_proportion = random.randint(0, size - 1)
        current_proportion = 0
        for token, frequency in token_counter.items():
            current_proportion += frequency
            if random_proportion < current_proportion:
                return token

    def _get_number_of_syllables(self, word):
        counter = Counter(word)
        return sum([counter[letter] for letter in self.russian_vowels])
            
    def _is_chain_legal(self, chain, is_prefix=False):
        # TODO: check different accent variants
        syllables = 0
        accents = []
        if is_prefix:
            accents.append(-1)
        for word in chain:
            curr_syllables = self._get_number_of_syllables(word)
            if curr_syllables > 1:
                curr_accents = Phonetics.get_word_accent(word)
                if len(curr_accents) == 0:
                    return False
                accents.append(syllables + self._get_number_of_syllables(word[:curr_accents[0]]))
            syllables += curr_syllables
        
        # print(chain, accents)
        for i in range(len(accents) - 1):
            if (accents[i + 1] - accents[i]) % 2 == 1:
                return False
        return True

    def _is_first_token_legal(self, token):
        if self._get_number_of_syllables(token) < 2:
            return True
        accents = Phonetics.get_word_accent(token)
        for possible_accent in accents:
            if self._get_number_of_syllables(token[:possible_accent]) % 2 == 1:
                return True
        return False
    
    def _is_prefix_legal(self, chain):
        return self._is_chain_legal(chain, is_prefix=True)
            
    def _make_next_token(self, is_even_line, cur_number_of_syllables,
                         new_sentence_tokens, max_iterations=MAX_RANDOM_ITER):
        chain = tuple(new_sentence_tokens[-self.depth:])
        new_token = self._make_random_token(chain)
        iter_count = 1
        while self._get_number_of_syllables(new_token) + cur_number_of_syllables \
                > self.number_of_syllables[is_even_line]:
            new_token = self._make_random_token(chain)
            iter_count += 1
            if iter_count > max_iterations:
                return None
        
        return new_token

    def _make_initial_token(self, max_iterations=MAX_RANDOM_ITER):
        new_token = self._make_random_token()
        iteration_count = 0
        while not (new_token.isalpha() and self._is_first_token_legal(new_token)) and iteration_count < max_iterations:
            new_token = self._make_random_token()
            iteration_count += 1

        if iteration_count == max_iterations:
            raise ValueError("unable to choose a random word to start with, "
                             "make sure your text set contains any words "
                             "and try again")

        return new_token

    def _format_token(self, token, previous_token):
        # suppose most punctuators may be followed by space
        # except examples like Anna-Maria, format_token, Hershey's
        if token.isalnum() or token in "([{«<":
            return " {}".format(token) if previous_token.strip().isalnum() else token
        else:
            return "{} ".format(token) if token not in ("-_'/") else token

    def _make_sentence_string(self, tokens):
        sentence = []
        for token in tokens:
            sentence.append(self._format_token(token, sentence[-1]) if sentence else token)
        return ''.join(sentence).strip()

    def _generate_line(self, is_even_line):
        words_sequence = None
        while (words_sequence is None) or (not self._is_prefix_legal(words_sequence)):
            words_sequence = [self._make_initial_token()]
            cur_number_of_syllables = self._get_number_of_syllables(words_sequence[0])
            
            tries_num = 0
            while cur_number_of_syllables != self.number_of_syllables[is_even_line]:
                if tries_num >= MAX_RANDOM_ITER:
                    tries_num = 0
                    words_sequence = [self._make_initial_token()]
                    cur_number_of_syllables = self._get_number_of_syllables(words_sequence[0])
                else:
                    new_token = self._make_next_token(is_even_line, cur_number_of_syllables, words_sequence)
                    while new_token is None:
                        tries_num += 1
                        poped_word = words_sequence.pop()
                        cur_number_of_syllables -= self._get_number_of_syllables(poped_word)
                        if len(words_sequence) > 0:
                            new_token = self._make_next_token(is_even_line, cur_number_of_syllables, words_sequence)
                        else:
                            words_sequence = [self._make_initial_token()]
                            cur_number_of_syllables = self._get_number_of_syllables(words_sequence[0])
                            new_token = self._make_next_token(is_even_line, cur_number_of_syllables, words_sequence)
                    words_sequence.append(new_token)
                    cur_number_of_syllables += self._get_number_of_syllables(new_token)

        return ' '.join(words_sequence)
    
    def generate_perashok(self):
        lines = []
        for i in range(4):
            lines.append(self._generate_line(i % 2 == 0))
        return '\n'.join(lines)
    
    def dump_self(self, filename):
        with open(filename, 'wb') as dump_file:
            pickle.dump(self.frequencies, dump_file)
            
    def load_dumped(self, filename):
        with open(filename, 'rb') as dumped_file:
            self.frequencies = pickle.load(dumped_file)


def create_and_dump_generator(depth, foldername, dump_filename):
    directory = join(settings.BASE_DIR, 'static', foldername)
    perashki = [join(directory, f) for f in listdir(directory) if isfile(join(directory, f))]

    generator = MarkovChainsGenerator(depth)

    for perashok_file in perashki:
        with open(perashok_file, encoding='utf-8') as input_stream:
            for i, line in enumerate(input_stream.readlines()):
                line = line.strip()
                for tokens in tokenize_without_punctuation(line):
                    generator.calculate_probabilities(tokens)
    # DEBUG            
    print(generator.get_probabilities_table())
    
    generator.dump_self(dump_filename)


def train_ngram_model(foldername='constitution', dump_filename=join(settings.BASE_DIR, 'static', 'generator.pickle')):
    create_and_dump_generator(depth=2, foldername=foldername, dump_filename=dump_filename)


def make_random_perashok(foldername='constitution', dump_filename=join(settings.BASE_DIR, 'static', 'generator.pickle')):
    generator = MarkovChainsGenerator(2)
    generator.load_dumped(dump_filename)
    
    return generator.generate_perashok()
