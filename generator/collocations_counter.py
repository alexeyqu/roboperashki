from collections import defaultdict
from os import listdir
from os.path import isfile, join

def make_pair(word1, word2):
	return word1.strip() + ' ' + word2.strip()

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
	        	if len(words[i]) > 3 and len(words[i + 1]) > 3: # отсеиваем всякие "и вот"
		        	pair = make_pair(words[i], words[i + 1])
		        	pairs_count[pair] += 1
		        	pairs.add(pair)

# просто частотные пары
print(sorted([(value, key) for key, value in pairs_count.items()], reverse=True)[:30])


def t_measure(word1, word2):
	return (pairs_count[make_pair(word1, word2)] - tokens_count[word1] * tokens_count[word2]) / pairs_count[make_pair(word1, word2)] ** 0.5

def get_k_best_collocations(k=50, measure_function=t_measure):
	measures = []
	for pair in pairs:
		measures.append((measure_function(*pair.split()), pair))

	return sorted(measures)[:k]


print('\n'.join(map(str, get_k_best_collocations())))