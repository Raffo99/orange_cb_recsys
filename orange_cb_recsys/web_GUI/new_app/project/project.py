from .module import ItemsContentAnalyzerModule, UsersContentAnalyzerModule, RatingsContentAnalyzerModule, \
    RecommenderSystemModule, PossiblePageStatus


class Project(object):
    def __init__(self, ca_algorithms, recsys_algorithms, dbpedia_classes):
        self.modules = {
            "ContentAnalyzer": {
                "Items": ItemsContentAnalyzerModule(ca_algorithms, dbpedia_classes),
                "Users": UsersContentAnalyzerModule(ca_algorithms, dbpedia_classes),
                "Ratings": RatingsContentAnalyzerModule(ca_algorithms, dbpedia_classes)
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

    def is_content_analyzer_complete(self, type_content):
        if type_content in self.modules["ContentAnalyzer"].keys():
            return self.content_analyzer[type_content].is_complete()
        return False


