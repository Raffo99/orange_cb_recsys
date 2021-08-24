import logging
import io
import sys

from .module import ItemsContentAnalyzerModule, UsersContentAnalyzerModule, RatingsContentAnalyzerModule, \
    RecommenderSystemModule, PossiblePageStatus, EvalModule
from threading import Thread
from orange_cb_recsys.script_handling import script_run
from orange_cb_recsys.utils.const import logger


def run_script(project, script):
    # old_stderr = sys.stderr
    # new_stderr = io.StringIO()
    # sys.stderr = new_stderr

    # log_capture_string = io.StringIO()
    try:
        project.logger.close()
    except:
        print("No logger to close")

    project.logger = io.StringIO()
    ch = logging.StreamHandler(project.logger)
    # ch = logging.StreamHandler(log_capture_string)
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter("<br> %(asctime)s - %(levelname)s - %(message)s")
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    script_run(script)

    # log_com = log_capture_string.getvalue()

    # print("err: " + new_stderr.getvalue())
    # sys.stderr = old_stderr
    project.running = False


class Project(object):
    def __init__(self, ca_algorithms, recsys_algorithms, eval_algorithms, dbpedia_classes):
        self.__logger = io.StringIO()
        self.__running = False
        self.modules = {
            "ContentAnalyzer": {
                "Items": ItemsContentAnalyzerModule(ca_algorithms, dbpedia_classes),
                "Users": UsersContentAnalyzerModule(ca_algorithms, dbpedia_classes),
                "Ratings": RatingsContentAnalyzerModule(ca_algorithms, dbpedia_classes)
            },
            "RecSys": RecommenderSystemModule(recsys_algorithms),
            "EvalModel": EvalModule(eval_algorithms)
        }
        self.name = "projectName"
        self.save_path = "./projects/"

    @property
    def running(self):
        return self.__running

    @running.setter
    def running(self, new_running):
        self.__running = new_running

    @property
    def logger(self):
        return self.__logger

    @logger.setter
    def logger(self, new_log):
        self.__logger = new_log

    def get_current_log(self):
        try:
            full_log = self.__logger.getvalue()
            if not self.running and not self.logger.closed:
                self.logger.close()
            print(full_log)
            return "Script started" + full_log
        except:
            return "CLOSED"

    def run(self, script):
        if not self.running:
            self.running = True
            t = Thread(target=run_script, args=(self, script,))
            t.start()
            return True
        return False

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

    @property
    def eval_model(self):
        return self.modules["EvalModel"]

    def is_first_project(self):
        return self.recommender_system.get_page_status("Upload") == PossiblePageStatus.DISABLED

    def is_content_analyzer_complete(self, type_content):
        if type_content in self.modules["ContentAnalyzer"].keys():
            return self.content_analyzer[type_content].is_complete()
        return False


