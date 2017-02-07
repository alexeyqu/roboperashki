from collections import defaultdict
from os import listdir
from os.path import isfile, join

from django.conf import settings

def make_pair(word1, word2):
    return '{} {}'.format(word1, word2)

def get_pos(tagged_word):
    return tagged_word.split(':')[-1]

def get_lemma(tagged_word):
    return tagged_word.split(':')[1]

def get_form(tagged_word):
    return tagged_word.split(':')[0]

def collocation_from_tagged(tagged_collocation):
    word1, word2 = tagged_collocation.split()
    return '{} {}'.format(get_form(word1), get_form(word2))

class CollocationCounter:
    def __init__(self, pos_pair_list=[('NOUN', 'NOUN')], perashki_dir=settings.PERASHKI_TAGGED_DIR):
        self.good_pos_combinations = set(pos_pair_list)
        self.perashki_dir = perashki_dir
        self.perashki_files = [join(perashki_dir, f) for f in listdir(perashki_dir) if isfile(join(perashki_dir, f))]

    def if_legal_pair_pos(self, word1, word2):
        pair_pos = (get_pos(word1), get_pos(word2))
        return pair_pos in self.good_pos_combinations

    def t_measure(self, word1, word2):
        c_pair = self.pairs_count[make_pair(word1, word2)]
        word1 = get_lemma(word1)
        word2 = get_lemma(word2)
        return (c_pair - (self.tokens_count[word1] * self.tokens_count[word2] * len(self.pairs_count) / len(self.tokens_count) ** 2)) / (c_pair ** 0.5)

    def get_k_best_collocations(self, k=50, measure_function=t_measure):
        self.pairs_count = defaultdict(int)
        self.tokens_count = defaultdict(int)

        pairs = set()

        for perashok_file in self.perashki_files:
            with open(perashok_file, encoding='utf-8') as input_stream:
                for line in input_stream.readlines():
                    words = line.split()
                    for w in words:
                        self.tokens_count[get_lemma(w)] += 1
                    for i in range(len(words) - 1):
                        if self.if_legal_pair_pos(words[i], words[i + 1]):
                            pair = make_pair(words[i], words[i + 1])
                            self.pairs_count[pair] += 1
                            pairs.add(pair)
        measures = []
        for pair in pairs:
            measures.append((-measure_function(self, *pair.split()), pair))

        return list(map(collocation_from_tagged, [c for measure, c in sorted(measures) if measure < -1.0][:k]))


def main():
    counter = CollocationCounter()
    # просто частотные пары
    # print('частотные пары')
    # print(sorted([(value, collocation_from_tagged(key)) for key, value in pairs_count.items()], reverse=True)[:30])
    # поиск 2-коллокаций с дефолтными параметрами (t-мера, 50 лучших)
    print('t-мера:')
    print(', '.join(map(collocation_from_tagged, [c for measure, c in counter.get_k_best_collocations()])))

if __name__ == '__main__':
	main()
