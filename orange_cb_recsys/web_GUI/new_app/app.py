import io
import logging

import pandas as pd
import os
import yaml
import json
import pickle

from flask import Flask, render_template, request, redirect, url_for
from werkzeug.utils import secure_filename
from os.path import join, dirname, realpath
from pathlib import Path

from orange_cb_recsys.utils.const import logger
from orange_cb_recsys.utils.load_content import load_content_instance
from orange_cb_recsys.content_analyzer.content_representation.content import Content

from utils.algorithms import get_ca_algorithms
from utils.algorithms import get_recsys_algorithms
from utils.forms import allowed_file, is_pathname_valid, get_dbpedia_classes
from project import Project, ContentAnalyzerModule, PossiblePageStatus, AnalyzerType

from orange_cb_recsys.script_handling import script_run
import sys


app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'
app.config['UPLOAD_FOLDER'] = join(dirname(realpath(__file__)), 'uploads\\')
app.config["PROJECTS_FOLDER"] = join(dirname(realpath(__file__)), 'projects\\')


def all_test(dictionary):
    return all(len(sub_class['params']) == 0 for sub_class in filter(lambda sc: 'params' in sc, dictionary['sub_classes']))


app.jinja_env.globals.update(all_python=all_test)

# Global variable for the current project
dbpedia_classes = get_dbpedia_classes()
current_project = Project(get_recsys_algorithms(), dbpedia_classes)


@app.route('/', methods=["POST", "GET"])
def index():
    global current_project

    list_errors = []

    if request.method == 'POST':
        if "nameProject" in request.form:
            if request.form["nameProject"] != "":
                current_project.name = request.form["nameProject"]
            else:
                list_errors.append("Project name is blank!")
            if is_pathname_valid(request.form["savePath"]):
                current_project.save_path = request.form["savePath"]
            else:
                list_errors.append("Save path is invalid!")
        else:
            current_project = Project(get_recsys_algorithms(), dbpedia_classes)
            current_project.content_analyzer_items.set_page_status("Upload", PossiblePageStatus.INCOMPLETE)
            current_project.content_analyzer_users.set_page_status("Upload", PossiblePageStatus.INCOMPLETE)
            current_project.content_analyzer_ratings.set_page_status("Upload", PossiblePageStatus.INCOMPLETE)
            current_project.recommender_system.set_page_status("Upload", PossiblePageStatus.INCOMPLETE)

    return render_template("index.html", project=current_project, list_errors=list_errors)


@app.route('/content-analyzer/upload', methods=['POST', 'GET'])
def ca_upload():
    """
    Page where the user can select the dataset to use in the content analyzer and the output directory.
    It can return the page of upload, or redirect to the next stage of the content analyzer if the method is POST and
    the dataset is a correct dataset.
    """
    global current_project

    content_analyzer_type = request.args.get("type")

    if current_project.is_first_project() \
            or content_analyzer_type not in current_project.content_analyzer_types \
            or current_project.content_analyzer[content_analyzer_type].get_page_status("Upload") == PossiblePageStatus.DISABLED:
        return redirect(url_for("index"))

    list_errors = []
    content_analyzer = current_project.content_analyzer[content_analyzer_type]

    if request.method == 'POST':
        if is_pathname_valid(request.form["outputDir"]):
            content_analyzer.output_directory = request.form["outputDir"]
        else:
            list_errors.append("Wrong output directory!")

        try:
            old_path = content_analyzer.source_path
            content_analyzer.source_path = request.form['pathDataset']

            # TODO: Support dat
            if content_analyzer.source_type == "csv":
                df = pd.read_csv(content_analyzer.source_path)
                content_analyzer.fields_list = list(df.columns.values)
            elif content_analyzer.source_type == "json":
                data = json.load(open(content_analyzer.source_path))
                content_analyzer.fields_list = list(data[0].keys())

            content_analyzer.clear_fields()
            content_analyzer.clear_id_fields()

            content_analyzer.set_page_status("Upload", PossiblePageStatus.COMPLETE)
            content_analyzer.set_page_status("Fields", PossiblePageStatus.INCOMPLETE)
            content_analyzer.set_page_status("Algorithms", PossiblePageStatus.DISABLED)
            return redirect(url_for('ca_fields') + "?type=" + content_analyzer_type)
        except Exception:
            content_analyzer.source_path = old_path
            list_errors.append("Error during processing dataset!")

    return render_template('/content-analyzer/upload.html', project=current_project, list_errors=list_errors,
                           content_analyzer=content_analyzer, content_type=content_analyzer_type)


@app.route('/content-analyzer/fields', methods=['POST', 'GET'])
def ca_fields():
    """
    Page where the user can select what fields serialize from the dataset and what field is a field id.
    """
    global current_project

    content_analyzer_type = request.args.get("type")

    if current_project.is_first_project() \
            or content_analyzer_type not in current_project.content_analyzer_types \
            or current_project.content_analyzer[content_analyzer_type].get_page_status("Fields") == PossiblePageStatus.DISABLED:
        return redirect(url_for("index"))

    content_analyzer = current_project.content_analyzer[content_analyzer_type]

    if request.method == "POST":
        new_fields = dict(request.form.items(multi=False))
        for key in list(content_analyzer.fields_selected):
            if not(key in list(map(lambda x: ContentAnalyzerModule.convert_key(x), new_fields))):
                content_analyzer.pop_field(key)

        temp_fields_id = []
        for key, value in new_fields.items():
            if "__fieldid" in key:
                temp_fields_id.append(key.replace("__fieldid", ""))
            elif not (ContentAnalyzerModule.convert_key(key) in content_analyzer.fields_selected):
                content_analyzer.set_field(key, [])

        content_analyzer.id_fields_name = temp_fields_id

        if not content_analyzer.fields_selected:
            # TODO: Dare errore nel caso in cui fields è vuoto
            return "ERRORE"
        else:
            content_analyzer.order_fields()

            content_analyzer.set_page_status("Fields", PossiblePageStatus.COMPLETE)
            content_analyzer.set_page_status("Algorithms", PossiblePageStatus.INCOMPLETE)
            content_analyzer.set_page_status("Exogenous", PossiblePageStatus.INCOMPLETE)
            return redirect(url_for('ca_settings') + "?type=" + content_analyzer_type)

    return render_template('/content-analyzer/fields.html', fields=content_analyzer.fields_list,
                           project=current_project, content_analyzer=content_analyzer,
                           content_type=content_analyzer_type)


@app.route('/content-analyzer/algorithms', methods=['POST', 'GET'])
def ca_settings():
    """
    Page where the user can select what algorithm to use for every field selected, and also what parameter to use
    for every algorithm, it NOT CHECKS the correctness of the parameters!!
    """
    global current_project

    content_analyzer_type = request.args.get("type")

    if current_project.is_first_project() \
            or content_analyzer_type not in current_project.content_analyzer_types \
            or current_project.content_analyzer[content_analyzer_type].get_page_status("Algorithms") == PossiblePageStatus.DISABLED:
        return redirect(url_for("index"))

    content_analyzer = current_project.content_analyzer[content_analyzer_type]

    # TODO: This code needs to be execute in the class, not here
    content_analyzer.content_production_algorithms, \
        content_analyzer.preprocess_algorithms, \
        content_analyzer.memory_interfaces,\
        content_analyzer.exogenous_algorithms,\
        content_analyzer.ratings_algorithms = get_ca_algorithms()

    return render_template('/content-analyzer/settings.html', fields=content_analyzer.fields_selected,
                           project=current_project, content_analyzer=content_analyzer,
                           content_type=content_analyzer_type)


@app.route('/content-analyzer/exogenous', methods=["POST", "GET"])
def ca_exogenous():
    global current_project

    content_analyzer_type = request.args.get("type")

    if current_project.is_first_project() \
            or content_analyzer_type not in current_project.content_analyzer_types \
            or current_project.content_analyzer[content_analyzer_type].get_page_status("Exogenous") == PossiblePageStatus.DISABLED:
        return redirect(url_for("index"))

    return render_template('content-analyzer/exogenous.html', project=current_project,
                           content_type=content_analyzer_type)


@app.route('/_representationformcreator', methods=['POST'])
def representation_form_creator():
    """
    Support page for the content analyzer, it creates a dynamic page with the representations of a field.
    In the dynamic page, for every representation, the user can change the id and every parameter of the representation.
    If the field doesn't have a representation yet, it assigns to the field a new representation list, with a single
    representation, the algorithm of the representation is taken in input
    Every input is taken in a the json data of a POST request, ("algorithm_name", "field_name", "has_representation")
    """
    global current_project

    content_analyzer = current_project.content_analyzer[request.json["content_type"]]
    fields = content_analyzer.fields_selected

    has_representation = request.json['has_representation']

    if has_representation:
        field_name = request.json["field_name"]
        representations = fields[field_name]
    else:
        if request.json["content_type"] == "Ratings":
            algorithms = content_analyzer.ratings_algorithms
        else:
            algorithms = content_analyzer.content_production_algorithms

        algorithm = [a for a in algorithms if a["name"] == request.json['algorithm_name']][0]

        if request.json["content_type"] == "Ratings":
            representations = [{
                'id': 'default',
                'algorithm': algorithm
            }]
        else:
            memory_interfaces = {
                "algorithms": content_analyzer.memory_interfaces,
                "value": content_analyzer.memory_interfaces[0]["name"],
                "use": False
            }

            representations = [{
                'id': 'default',
                'algorithm': algorithm,
                'preprocess': content_analyzer.preprocess_algorithms,
                'memory_interfaces': memory_interfaces
            }]

    return render_template("/content-analyzer/helpers/_representationformcreator.html", representations=representations)


@app.route('/ca-update-representations', methods=['POST', 'GET'])
def ca_update_representations():
    """
    Support page used for update the fields representations in the content analyzer, the input can be send in
    the json data of a POST request or in the form data of a POST request
    There are 2 main function:
        -  Update all the representations of a field
            In the data there isn't the field 'delete_representation' and there is the list of representations to
            assign to the field in json format
        -  Delete a single representation of a field
            There is the field 'delete_representation' and there is the index of the representation to delete
            from the field
    Both of them has the field "field_name", the name of the field to update/delete
    """
    global current_project

    if current_project.is_first_project():
        return redirect(url_for("index"))

    if request.form:
        if not("delete_representation" in request.form):
            delete_representation = False
            new_representations = json.loads(request.form['representations'])
        else:
            delete_representation = True
            index_representation = request.form['index_representation']
        content_type = request.form['content_type']
        field_name = request.form['field_name']
    else:
        if not("delete_representation" in request.json):
            delete_representation = False
            new_representations = request.json['representations']
        else:
            delete_representation = True
            index_representation = request.json['index_representation']
        field_name = request.json['field_name']
        content_type = request.json['content_type']

    content_analyzer = current_project.content_analyzer[content_type]
    if delete_representation:
        content_analyzer.pop_representation(field_name, index_representation)
    else:
        content_analyzer.set_field(field_name, new_representations)

    if any(len(representation) > 0 for representation in content_analyzer.fields_selected.values()):
        content_analyzer.set_page_status("Algorithms", PossiblePageStatus.COMPLETE)
    else:
        content_analyzer.set_page_status("Algorithms", PossiblePageStatus.INCOMPLETE)

    return ""


@app.route("/recsys/upload", methods=['POST', 'GET'])
def recsys_upload():
    global current_project

    if current_project.is_first_project() \
            or current_project.recommender_system.get_page_status("Upload") == PossiblePageStatus.DISABLED:
        return redirect(url_for("index"))

    list_errors = []
    if request.method == 'POST':
        items_path = request.form["pathItems"]
        users_path = request.form["pathUsers"]
        output_directory = request.form["outputDir"]
        ratings_path = request.form["pathRatings"]
        try:
            if items_path == "" and current_project.recommender_system.items_path != "" \
                    and not is_pathname_valid(items_path):
                list_errors.append("Path to items is invalid.")
            else:
                current_project.recommender_system.items_path = items_path

            if users_path == "" and current_project.recommender_system.users_path != "" \
                    and not is_pathname_valid(users_path):
                list_errors.append("Path to users is invalid.")
            else:
                current_project.recommender_system.users_path = users_path

            if output_directory == "" and current_project.recommender_system.output_directory != "" \
                    and not is_pathname_valid(output_directory):
                list_errors.append("Output directory is invalid.")
            else:
                current_project.recommender_system.output_directory = output_directory

            if ratings_path == "" and current_project.recommender_system.ratings_path != ""\
                    and not is_pathname_valid(ratings_path):
                list_errors.append("Path to ratings is invalid.")
            else:
                current_project.recommender_system.ratings_path = ratings_path

            if len(list_errors) == 0:
                list_files = [f for f in os.listdir(items_path) if os.path.isfile(join(items_path, f)) and ".xz" in f]
                file_to_check = list_files[0]
                content = load_content_instance(items_path, file_to_check.replace(".xz", ""))
                if isinstance(content, Content):
                    current_project.recommender_system.content = content
                    current_project.recommender_system.set_page_status("Upload", PossiblePageStatus.COMPLETE)
                    current_project.recommender_system.set_page_status("Representations", PossiblePageStatus.INCOMPLETE)
                    return redirect(url_for('recsys_representations'))
                else:
                    list_errors.append("Invalid items file in items directory <br>(<b>'" + items_path + "'</b>)")
        except IndexError:
            list_errors.append("There is no valid file in the items directory <br>(<b>'" + items_path + "'</b>)")
        except FileNotFoundError:
            list_errors.append("<b>'" + items_path + "'</b> is not a valid directory.")
        except OSError:
            list_errors.append("Wrong syntax in path to content.")

    return render_template("./recsys/upload.html", list_errors=list_errors, project=current_project)


@app.route("/recsys/representations", methods=['POST', 'GET'])
def recsys_representations():
    global current_project

    if current_project.is_first_project() \
            or current_project.recommender_system.get_page_status("Representations") == PossiblePageStatus.DISABLED:
        return redirect(url_for("index"))

    return render_template("./recsys/representations.html",
                           fields_representations=current_project.recommender_system.content.field_dict,
                           project=current_project)


@app.route("/update-recsys-algorithm", methods=["POST"])
def update_recsys_algorithm():
    global current_project

    if request.method == "POST":
        current_project.recommender_system.algorithms = request.json["algorithms"]
        current_project.recommender_system.selected_algorithm = request.json["selectedAlgorithm"]
        current_project.recommender_system.field_dict = request.json["listFields"]

    return ""


@app.route("/execute-modules", methods=["POST", "GET"])
def execute_modules():
    global current_project

    if request.method == "POST":
        if request.json["module"] == "ContentAnalyzer":
            old_stderr = sys.stderr
            new_stderr = io.StringIO()
            sys.stderr = new_stderr


            log_capture_string = io.StringIO()
            ch = logging.StreamHandler(log_capture_string)
            ch.setLevel(logging.DEBUG)
            formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
            ch.setFormatter(formatter)
            logger.addHandler(ch)

            print(current_project.content_analyzer.produce_config_file())
            script_run(current_project.content_analyzer.produce_config_file())
            log_com = log_capture_string.getvalue()
            log_capture_string.close()

            print("log: " + log_com)
            # print("err: " + new_stderr.getvalue())

            sys.stderr = old_stderr
            return json.dumps({"result": log_com.replace("\n", "<br>")})

    return render_template("./execute.html", project=current_project)


@app.route("/save-config-file", methods=["GET", "POST"])
def save_config_file():
    global current_project

    if current_project is not None and request.method == "POST":
        module = request.json["module"]

        try:
            config_file = current_project.modules[module].produce_config_file()

            with open(current_project.save_path + "/" + current_project.name + "/content_analyzer_config.json", "w") as outfile:
                json.dump(config_file, outfile, indent=4)

            with open(current_project.save_path + "/" + current_project.name + "/content_analyzer_config.yaml", "w") as outfile:
                yaml.dump(config_file, outfile)

        except KeyError:
            return json.dumps({"result": "False"})

    else:
        return json.dumps({"result": "False"})

    return json.dumps({"result": "True"})


@app.route("/save-current-project", methods=["GET", "POST"])
def save_current_project():
    """
    Support page used to save the variable current_project
    """
    global current_project

    if current_project is None:
        return json.dumps({"result": "False"})

    delete_old = request.json["delete_old"]

    try:
        final_path = current_project.save_path + "/" + current_project.name + "/"
        Path(final_path).mkdir(parents=True, exist_ok=True)
        if os.path.exists(final_path + "/" + current_project.name + ".prj") and not delete_old:
            return json.dumps({"result": "Question"})
        with open(final_path + current_project.name + ".prj", 'wb') as output:
            pickle.dump(current_project, output, pickle.HIGHEST_PROTOCOL)
    except TypeError as e:
        print(str(e))
        return json.dumps({"result": "False"})

    return json.dumps({"result": "True"})


@app.route("/load-new-project", methods=["GET", "POST"])
def load_new_project():
    """
    Support page used to load a project file, it use the file passed in the POST request with some checks on the file
    """
    global current_project

    file = request.files['pathProject']

    if file.filename == '':
        # TODO: bisogna dare un errore
        print('Errore upload')

    if file and file.filename.endswith(".prj"):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        with open(os.path.join(app.config['UPLOAD_FOLDER'], filename), 'rb') as input_project:
            current_project = pickle.load(input_project)

    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run()
