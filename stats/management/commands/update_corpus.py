from stats.get_perashki_corpora import get_corpus_from_web, make_tagged_corpus
import shutil
import os
import logging

from django.conf import settings
from django.core.management.base import LabelCommand

class Command(LabelCommand):

    def clear_directory(self, directory):
        print('Preparing directory: {}'.format(directory))
        if os.path.exists(directory):
            shutil.rmtree(directory)
        os.makedirs(directory)

    def handle_label(self, label, **args):
        if label != "retag_only":
            self.clear_directory(settings.PERASHKI_UNTAGGED_DIR)
            print('Starting scrapy spider. Relax and have a drink, corpus retrieval may take a while')
            get_corpus_from_web()
            print('Raw corpus retrieved')
            
        print('Starting linguistic preprocessing')
        self.clear_directory(settings.PERASHKI_TAGGED_DIR)
        make_tagged_corpus()
        print('Got things done. Statistics should work now!')
