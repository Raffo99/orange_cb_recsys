from unittest import TestCase
import os
import pathlib as pl

from orange_cb_recsys.content_analyzer.embeddings.embedding_learner.doc2vec import GensimDoc2Vec
from orange_cb_recsys.content_analyzer.information_processor.nlp import NLTK
from orange_cb_recsys.content_analyzer.raw_information_source import JSONFile

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(THIS_DIR, '../../../../datasets/movies_info_reduced.json')


class TestGensimDoc2Vec(TestCase):
    def test_fit(self):
        model_path = os.path.join(THIS_DIR, "/model_test_Doc2Vec")
        learner = GensimDoc2Vec(model_path, True)
        learner.fit(source=JSONFile(file_path), field_list=["Plot", "Genre"], preprocessor_list=[NLTK()])
        model_path += ".model"

        self.assertEqual(learner.get_embedding("ace").any(), True)
        self.assertEqual(pl.Path(model_path).resolve().is_file(), True)
