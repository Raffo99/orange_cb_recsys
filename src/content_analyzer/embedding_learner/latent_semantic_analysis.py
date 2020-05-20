import gensim

from src.content_analyzer.embedding_learner.embedding_learner import LatentSemanticAnalysis
from src.content_analyzer.information_processor.information_processor import InformationProcessor
from src.content_analyzer.raw_information_source import RawInformationSource


class GensimLatentSemanticAnalysis(LatentSemanticAnalysis):
    """
    Class that implements latent semantic analysis using Gensim
    """
    def __init__(self, source: RawInformationSource, preprocessor: InformationProcessor):
        super().__init__(source, preprocessor)

    def __str__(self):
        return "GensimLatentSemanticAnalysis"

    def __repr__(self):
        return "< GensimLatentSemanticAnalysis :" + \
                "source = " + str(self.__source) + \
                "preprocessor = " + str(self.__preprocessor) + " >"

    @staticmethod
    def create_dictionary(self, docs):
        return gensim.corpora.Dictionary[docs]

    @staticmethod
    def create_wod_docs_matrix(self, docs, dictionary) -> gensim.corpora.dictionary.Dictionary:
        return [dictionary.doc2bow(doc) for doc in docs]

