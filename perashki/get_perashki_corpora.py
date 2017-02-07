from collections import defaultdict

from os import listdir
from os.path import isfile, join
import pymorphy2

from lxml import html
import bs4

from scrapy.spiders import CrawlSpider, Rule
from scrapy.crawler import CrawlerProcess
from scrapy.linkextractors import LinkExtractor

from django.conf import settings

def get_corpus_from_web(perashki_dir=settings.PERASHKI_UNTAGGED_DIR):
    def get_int(container):
        string = html.tostring(container, method="text", encoding='unicode').strip()
        if not string[0].isdigit():
            string = string[1:]
        return int(string)

    def get_overall(container):
        return get_int(container.xpath(".//span[@class='club']")[0]) + \
               get_int(container.xpath(".//span[@class='All']")[0])
    
    class WikiSpider(CrawlSpider):
        name = "perashki_spider"
        allowed_domains = ["perashki.ru"]
        start_urls = ["http://perashki.ru/Piro/All/?page=1"]
        
        rules = (
            Rule(
                LinkExtractor(allow='http://perashki.ru/Piro/All/\?page=\d+$'),
                callback='parse_item',
                follow=True,
            ),
        )
        
        def parse_item(self, response):
            root = html.fromstring(response.body)
            
            for story_count, piro_box in enumerate(root.xpath(".//div[@class='PiroBox']")):
                story_container = piro_box.xpath(".//div[@class='TextContainer']")[0]
                votes_container = piro_box.xpath(".//div[@class='Votes']")[0]
                
                favor = votes_container.xpath(".//div[@class='Info VoteFavorite']")[0]
                plus = votes_container.xpath(".//div[@class='Info VotePlus']")[0]
                minus = votes_container.xpath(".//div[@class='Info VoteMinus']")[0]
                
                favor_value = get_overall(favor)
                plus_value = get_overall(plus)
                minus_value = get_overall(minus)
                
                story_div = story_container.xpath(".//div[@class='Text']")[0]
                
                story_date = story_container.xpath(".//span[@class='date']")[0]
                story_author = story_container.xpath(".//a[contains(@class, 'User')]")[0]
                
                page_num = response.request.url.split('=')[-1]
                with open(os.path.join(settings.PERASHKI_UNTAGGED_DIR, 'perashki_{}_{}.txt'.format(page_num, story_count), 'w')) as fout:
                    print(html.tostring(story_date, method="text", encoding='unicode'), file=fout)
                    print(html.tostring(story_author, method="text", encoding='unicode').strip()[:-1], file=fout)
                    print(html.tostring(story_div, method="text", encoding='unicode').strip(), file=fout)
                    print(favor_value, plus_value, minus_value, file=fout)

    process = CrawlerProcess({})

    process.crawl(WikiSpider)
    process.start()


def get_pos(word, morph_parser):
    return morph_parser.parse(word)[0].tag.POS

def get_lemma(word, morph_parser):
    return morph_parser.parse(word)[0].normal_form


def make_tagged_corpus(perashki_dir=settings.PERASHKI_UNTAGGED_DIR, perashki_tagged_dir=settings.PERASHKI_UNTAGGED_DIR):
    perashki = [(join(perashki_dir, f), join(perashki_tagged_dir, f)) for f in listdir(perashki_dir) if isfile(join(perashki_dir, f))]
    morph = pymorphy2.MorphAnalyzer()
    
    for perashok_file, perashok_tagged_file in perashki:
        with open(perashok_file, encoding='utf-8') as input_stream, open(perashok_tagged_file, 'w', encoding='utf-8') as output_stream:
            for line in input_stream.readlines()[2:-1]:
                words = line.split()
                words_tagged = []
                for word in words:
                    words_tagged.append('{}:{}:{}'.format(word, get_lemma(word, morph), get_pos(word, morph)))
                print(*words_tagged, file=output_stream)
                

if __name__ == '__main__':
	make_tagged_corpus()
