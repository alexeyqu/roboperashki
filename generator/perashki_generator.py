import re
import argparse
import unittest
from collections import Counter, defaultdict
import random
from os import listdir
from os.path import isfile, join
import pickle

MAX_RANDOM_ITER = 1000

def tokenize(line):
    return re.findall(r"[^\W\d]+|[^\w\s]+|\s+|\d+", line, re.LOCALE & re.UNICODE)[::-1]


def output_tokens(input_stream, args):
    line = input_stream.readline()

    with open('output.txt', 'w', encoding='utf-8') as output_stream:
        for token in tokenize(line.strip()):
            print(token, file=output_stream)

class MarkovChainsGenerator:
    def __init__(self, depth):
        self.depth = depth
        self.frequencies = { True : defaultdict(Counter), False : defaultdict(Counter) }
        self.number_of_syllables = { True : 9, False : 8 }
        self.russian_vowels = ["ё", "у", "е", "ы", "а", "о", "э", "я", "и", "ю"]

    def calculate_probabilities(self, token_generator, is_even_line):
        current_tokens = []
        for index, token in enumerate(token_generator):
            for start in range(len(current_tokens) + 1):
                chain = tuple(current_tokens[start:])
                if len(chain) == 0 and index != 0:
                    continue
                self.frequencies[is_even_line][chain][token] += 1

            if len(current_tokens) == self.depth:
                current_tokens.pop(0)
            current_tokens.append(token)
            
    def get_probabilities_table(self):
        probabilities_table = {True : {}, False : {}}

        for line_type in [True, False]:
            for chain, token_counter in self.frequencies[line_type].items():
                size = sum(token_counter.values())
                probabilities_table[line_type][' '.join(chain)] = [(token, freq / size)
                                                        for token, freq
                                                        in sorted(token_counter.items())]

        return probabilities_table

    def _make_random_token(self, is_even_line, chain=tuple()):
        token_counter = self.frequencies[is_even_line][chain]

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
            
    def _make_next_token(self, is_even_line, cur_number_of_syllables,
                         new_sentence_tokens, max_iterations=MAX_RANDOM_ITER):
        chain = tuple(new_sentence_tokens[-self.depth:])
        new_token = self._make_random_token(is_even_line, chain)
        iter_count = 1
        while self._get_number_of_syllables(new_token) + cur_number_of_syllables \
                > self.number_of_syllables[is_even_line]:
            new_token = self._make_random_token(is_even_line, chain)
            iter_count += 1
            if iter_count > max_iterations:
                return None
        return new_token

    def _make_initial_token(self, is_even_line, max_iterations=MAX_RANDOM_ITER):
        new_token = self._make_random_token(is_even_line)
        iteration_count = 0
        while not new_token.isalpha() and iteration_count < max_iterations:
            new_token = self._make_random_token(is_even_line)
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
        words_sequence = [self._make_initial_token(is_even_line)]
        cur_number_of_syllables = self._get_number_of_syllables(words_sequence[0])
        while cur_number_of_syllables != self.number_of_syllables[is_even_line]:
            new_token = self._make_next_token(is_even_line, cur_number_of_syllables, words_sequence)
            while new_token is None:
                poped_word = words_sequence.pop()
                cur_number_of_syllables -= self._get_number_of_syllables(poped_word)
                if len(words_sequence) > 0:
                    new_token = self._make_next_token(is_even_line, cur_number_of_syllables, words_sequence)
                else:
                    words_sequence = [self._make_initial_token(is_even_line)]
                    cur_number_of_syllables = self._get_number_of_syllables(words_sequence[0])
                    new_token = self._make_next_token(is_even_line, cur_number_of_syllables, words_sequence)
            words_sequence.append(new_token)
            cur_number_of_syllables += self._get_number_of_syllables(new_token)
        return ' '.join(words_sequence[::-1])
    
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
    
def output_probabilities(input_stream, args):
    generator = MarkovChainsGenerator(args.depth)

    for line in input_stream:
        line = line.strip()
        generator.calculate_probabilities(filter(str.isalpha, tokenize(line)))

    with open('output.txt', 'w', encoding='utf-8') as output_stream:
        for chain, tokens in sorted(generator.get_probabilities_table().items()):
            print(chain, file=output_stream)
            for token, probability in tokens:
                print('  {tok}: {prob:.2f}'.format(tok=token, prob=probability),
                      file=output_stream)


def output_generated(input_stream, args):
    generator = MarkovChainsGenerator(args.depth)
    raw_text = input_stream.read()
    generator.calculate_probabilities(filter(lambda x: re.match("\S", x), tokenize(raw_text)))

    with open('output.txt', 'w', encoding='utf-8') as output_stream:
        print(generator.generate_text(args.size), file=output_stream)
        
def create_and_dump_generator(depth, dump_filename):
    perashki_dir = 'static/perashki/'
    perashki = [join(perashki_dir, f) for f in listdir(perashki_dir) if isfile(join(perashki_dir, f))]

    generator = MarkovChainsGenerator(depth)

    for perashok_file in perashki:
        with open(perashok_file, encoding='utf-8') as input_stream:
            for i, line in enumerate(input_stream.readlines()[2:]):
                line = line.strip()
                generator.calculate_probabilities(filter(str.isalpha, tokenize(line)), i % 2 == 0)
    generator.dump_self(dump_filename)

# dummy function, generating one perashok with default arguments
def make_random_perashok():
    #create_and_dump_generator(depth=2, dump_filename='static/generator.pickle')
    
    generator = MarkovChainsGenerator(2)
    generator.load_dumped('static/generator.pickle')
    
    return generator.generate_perashok()
