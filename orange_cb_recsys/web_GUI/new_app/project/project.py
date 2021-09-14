import logging
import io
import sys

from .module import ItemsContentAnalyzerModule, UsersContentAnalyzerModule, RatingsContentAnalyzerModule, \
    RecommenderSystemModule, PossiblePageStatus, EvalModule
from threading import Thread
from orange_cb_recsys.script.script_handling import handle_script_contents
from orange_cb_recsys.utils.const import logger, recsys_logger, eval_logger

import traceback
from importlib import reload


def run_script(project, script):
    old_stderr = sys.stderr
    new_stderr = io.StringIO()
    sys.stderr = new_stderr

    try:
        handle_script_contents(script)
    except Exception as e:
        traceback.print_exc()
        log_com = project.logger_content.getvalue() + project.logger_recsys.getvalue() + project.logger_eval.getvalue()
        project.full_log += log_com
        project.full_log += "<br> Exception: " + str(e)

    # project.logger.close()

    sys.stderr = old_stderr
    project.temp_log = "--- Script started ---" + project.logger_content.getvalue() + project.logger_eval.getvalue() \
                              + project.logger_recsys.getvalue() + "<br>--- Script ended ---<br>"
    project.full_log += project.temp_log

    project.init_loggers()
    project.running = False


class Project(object):
    def __init__(self, ca_algorithms, recsys_algorithms, eval_algorithms, dbpedia_classes):
        self.logger_content = io.StringIO()
        self.logger_recsys = io.StringIO()
        self.logger_eval = io.StringIO()
        self.init_loggers()
        self.full_log = ""
        self.temp_log = ""
        self.__running = False
        self.__modules = {
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
    def modules(self):
        return self.__modules

    def init_loggers(self):
        self.temp_log = ""

        self.logger_content = io.StringIO()
        self.logger_recsys = io.StringIO()
        self.logger_eval = io.StringIO()

        ch_content = logging.StreamHandler(self.logger_content)
        ch_recsys = logging.StreamHandler(self.logger_recsys)
        ch_eval = logging.StreamHandler(self.logger_eval)

        ch_content.setLevel(logging.DEBUG)
        ch_recsys.setLevel(logging.DEBUG)
        ch_eval.setLevel(logging.DEBUG)

        formatter = logging.Formatter("<br> %(asctime)s - %(levelname)s - %(message)s")

        ch_content.setFormatter(formatter)
        ch_recsys.setFormatter(formatter)
        ch_eval.setFormatter(formatter)

        logger.addHandler(ch_content)
        recsys_logger.addHandler(ch_recsys)
        eval_logger.addHandler(ch_eval)

    @property
    def running(self):
        return self.__running

    @running.setter
    def running(self, new_running):
        self.__running = new_running

    def get_current_log(self):
        if self.running:
            self.temp_log = "--- Script started ---" + self.logger_content.getvalue() + self.logger_eval.getvalue() \
                              + self.logger_recsys.getvalue()

            final_log = self.temp_log
        else:
            final_log = self.full_log
        return final_log

    def run(self, script):
        if not self.running:
            self.running = True
            self.temp_log = ""
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

    def produce_config_file(self, module, content_type=None):
        if module == "ContentAnalyzer":
            config_file = self.modules[module][content_type].produce_config_file()
        elif module == "RecSys":
            config_file = self.modules[module].produce_config_file()
        elif module == "EvalModel":
            recsys_config = self.recommender_system.produce_config_file() \
                if self.eval_model.is_recsys_from_project() else None
            config_file = self.modules[module].produce_config_file(recsys_config)
        return config_file


