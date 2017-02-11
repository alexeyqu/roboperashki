import unittest
import os

from django.conf import settings
from phonetics.accent_classifier import AccentClassifier
from phonetics.accent_dict import AccentDict
from phonetics.phonetics import Phonetics


class TestAccentClassifier(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.accent_dict = AccentDict(os.path.join(settings.BASE_DIR, "static", "dicts", "accents_dict"))

    def test_accent_classifier(self):
        self.assertEqual(Phonetics.get_word_accent('конституция', self.accent_dict), [7])
