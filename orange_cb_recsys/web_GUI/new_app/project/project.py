from module import ContentAnalyzerModule, RecommenderSystemModule


class Project(object):
    def __init__(self):
        self.content_analyzer = ContentAnalyzerModule()
        self.recommender_system = RecommenderSystemModule()
