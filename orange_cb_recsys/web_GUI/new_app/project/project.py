from .module import ContentAnalyzerModule, RecommenderSystemModule, PossiblePageStatus


class Project(object):
    def __init__(self, recsys_algorithms, dbpedia_classes):
        self.modules = {
            "ContentAnalyzer": {
                "Items": ContentAnalyzerModule(dbpedia_classes),
                "Users": ContentAnalyzerModule(dbpedia_classes),
                "Ratings": ContentAnalyzerModule(dbpedia_classes)
            },
            "RecSys": RecommenderSystemModule(recsys_algorithms)
        }
        self.name = "projectName"
        self.save_path = "./projects/"

    @property
    def content_analyzer_types(self):
        return self.modules["ContentAnalyzer"].keys()

    @property
    def content_analyzer(self):
        return self.modules["ContentAnalyzer"]

    @property
    def content_analyzer_items(self):
        return self.modules["ContentAnalyzer"]["Items"]

    @property
    def content_analyzer_users(self):
        return self.modules["ContentAnalyzer"]["Users"]

    @property
    def content_analyzer_ratings(self):
        return self.modules["ContentAnalyzer"]["Ratings"]

    @property
    def recommender_system(self):
        return self.modules["RecSys"]

    def is_first_project(self):
        return self.recommender_system.get_page_status("Upload") == PossiblePageStatus.DISABLED


