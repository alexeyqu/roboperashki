from collections import defaultdict
from os import listdir
from os.path import isfile, join
import pymorphy2

def make_pair(word1, word2):
	return word1.strip() + ' ' + word2.strip()

def get_pos(word, morph_parser):
	return morph_parser.parse(word)[0].tag.POS

def if_legal_pair_pos(word1, word2):
	# можно добавить ещё каких-нибудь pos-комбинаций, разумеется
	good_pos_combinations = set((("VERB", "NOUN"), 
								("NOUN", "VERB"), 
								("ADJF", "NOUN"), 
								("ADJS", "NOUN"), 
								("NOUN", "NOUN")))
	morph = pymorphy2.MorphAnalyzer()
	pair_pos = (get_pos(word1, morph), get_pos(word2, morph))
	# if pair_pos in good_pos_combinations:
	#    print(pair_pos, word1, word2)
	return pair_pos in good_pos_combinations


perashki_dir = 'perashki'
perashki = [join(perashki_dir, f) for f in listdir(perashki_dir) if isfile(join(perashki_dir, f))]

pairs_count = defaultdict(int)
tokens_count = defaultdict(int)

pairs = set()

for perashok_file in perashki:
    with open(perashok_file, encoding='utf-8') as input_stream:
    	for line in input_stream.readlines()[2:-1]:
	        words = line.split()
	        for w in words:
	        	tokens_count[w] += 1
	        for i in range(len(words) - 1):
	        	if if_legal_pair_pos(words[i], words[i + 1]):
	        		# TODO: попробовать поюзать здесь стеммер?
		        	pair = make_pair(words[i], words[i + 1])
		        	pairs_count[pair] += 1
		        	pairs.add(pair)


def t_measure(word1, word2):
	c_pair = pairs_count[make_pair(word1, word2)] 
	return (c_pair - (tokens_count[word1] * tokens_count[word2] * len(pairs_count) / len(tokens_count) ** 2)) / (c_pair ** 0.5)

def get_k_best_collocations(k=50, measure_function=t_measure):
	measures = []
	for pair in pairs:
		measures.append((measure_function(*pair.split()), pair))

	return sorted(measures)[:k]

def main():
	# просто частотные пары
	print('частотные пары')
	print(', '.join(sorted([(value, key) for key, value in pairs_count.items()], reverse=True)[:30]))
	# поиск 2-коллокаций с дефолтными параметрами (t-мера, 50 лучших)
	print('t-мера:')
	print(', '.join(map(str, get_k_best_collocations())))

if __name__ == '__main__':
	main()