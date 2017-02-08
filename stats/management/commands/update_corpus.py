from stats.get_perashki_corpora import get_corpus_from_web, make_tagged_corpus
import shutil
import os

from django.conf import settings

def clear_directory(directory):
    if os.path.exists(directory):
        shutil.rmtree(directory)
    os.makedirs(directory)

clear_directory(settings.PERASHKI_UNTAGGED_DIR)
get_corpus_from_web()

clear_directory(settings.PERASHKI_TAGGED_DIR)
make_tagged_corpus()
