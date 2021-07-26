from .module import ContentAnalyzerModule, RecommenderSystemModule, PossiblePageStatus


class Project(object):
    def __init__(self, recsys_algorithms, dbpedia_classes):
        self.modules = {
            "ContentAnalyzer": ContentAnalyzerModule(dbpedia_classes),
            "RecSys": RecommenderSystemModule(recsys_algorithms)
        }
        self.name = "projectName"
        self.save_path = "./projects/"

    @property
    def content_analyzer(self):
        return self.modules["ContentAnalyzer"]

    @property
    def recommender_system(self):
        return self.modules["RecSys"]

    def is_first_project(self):
        return self.content_analyzer.get_page_status("Upload") == PossiblePageStatus.DISABLED


