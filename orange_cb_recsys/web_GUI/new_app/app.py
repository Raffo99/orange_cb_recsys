import pandas as pd
import os
import yaml
import json
import pickle
import time

from flask import Flask, render_template, request, redirect, url_for
from werkzeug.utils import secure_filename
from os.path import join, dirname, realpath
from pathlib import Path

from orange_cb_recsys.utils.load_content import load_content_instance
from orange_cb_recsys.content_analyzer.content_representation.content import Content

from utils.algorithms import get_ca_algorithms, get_recsys_algorithms, get_eval_algorithms
from utils.forms import is_pathname_valid, get_dbpedia_classes
from project import Project, ContentAnalyzerModule, PossiblePageStatus

from orange_cb_recsys.script.script_handling import Run
import orange_cb_recsys.runnable_instances as r_i

from orange_cb_recsys.script.script_handling import handle_script_contents

Run.set_runnable_instances(r_i.get_classes())

app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'
app.config['UPLOAD_FOLDER'] = join(dirname(realpath(__file__)), 'uploads\\')
app.config["PROJECTS_FOLDER"] = join(dirname(realpath(__file__)), 'projects\\')


def all_test(dictionary):
    return all(len(sub_class['params']) == 0 for sub_class in filter(lambda sc: 'params' in sc, dictionary['sub_classes']))


app.jinja_env.globals.update(all_python=all_test)

# Global variable for the current project
try:
    dbpedia_classes = get_dbpedia_classes()
except Exception:
    print("Error while loading dbpedia classes, these won't be used")
    dbpedia_classes = []

current_project = Project(get_ca_algorithms(), get_recsys_algorithms(), get_eval_algorithms(), dbpedia_classes)


def check_contents(path_to_content, content_type):
    global current_project

    list_errors = []
    try:
        list_files = [f for f in os.listdir(path_to_content) if os.path.isfile(join(path_to_content, f)) and ".xz" in f]
        file_to_check = list_files[0]
        content = load_content_instance(path_to_content, file_to_check.replace(".xz", ""))
        if isinstance(content, Content):
            fields = {}
            for field in content.field_dict.items():
                representations = []
                if len(field[1].get_external_index()) > 0:
                    for representation in field[1].get_external_index():
                        representations.append(representation)
                    fields[field[0]] = representations

            current_project.recommender_system.fields_representations[content_type] = fields
            current_project.recommender_system.exogenous_techniques[content_type] = content.exogenous_rep_container.get_external_index()
        else:
            list_errors.append("Invalid items file in items directory <br>(<b>'" + path_to_content + "'</b>)")
    except FileNotFoundError:
        list_errors.append("<b>'" + path_to_content + "'</b> is not a valid directory.")
    except OSError:
        list_errors.append("Wrong syntax in path to content.")
    return list_errors


def get_fields_and_exogenous(content_type):
    global current_project

    fields = {field: [representation["id"] for representation in representations]
              for field, representations in current_project.content_analyzer[content_type].fields_selected.items()
              if len(representations) > 0}

    exogenous = [technique['content'][0]['params'][1]['value']
                 for technique in current_project.content_analyzer[content_type].exogenous_techniques
                 if 'content' in technique and len(technique['content'][0]['params']) > 0]

    current_project.recommender_system.fields_representations[content_type] = fields
    current_project.recommender_system.exogenous_techniques[content_type] = exogenous


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
            current_project = Project(get_ca_algorithms(), get_recsys_algorithms(), get_eval_algorithms(), dbpedia_classes)
            current_project.content_analyzer_items.set_page_status("Upload", PossiblePageStatus.INCOMPLETE)
            current_project.content_analyzer_users.set_page_status("Upload", PossiblePageStatus.INCOMPLETE)
            current_project.content_analyzer_ratings.set_page_status("Upload", PossiblePageStatus.INCOMPLETE)
            current_project.recommender_system.set_page_status("Upload", PossiblePageStatus.INCOMPLETE)
            current_project.eval_model.set_page_status("Upload", PossiblePageStatus.INCOMPLETE)

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
                data = json.load(open(content_analyzer.source_path, 'r', encoding="cp866"))
                content_analyzer.fields_list = list(data[0].keys())

            if content_analyzer_type != "Ratings":
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
        if request.args.get("type") == "Ratings":
            from_id_column = request.form["fromIdColumn"]
            to_id_column = request.form["toIdColumn"]
            score_column = request.form["scoreColumn"]
            timestamp_column = request.form["timestampColumn"]

            if [from_id_column, to_id_column, score_column] in [content_analyzer.fields_list] and \
                    (timestamp_column in [content_analyzer.fields_list, None]):
                content_analyzer.from_id_column = from_id_column
                content_analyzer.to_id_column = to_id_column
                content_analyzer.score_column = score_column
                content_analyzer.timestamp_column = timestamp_column
        else:
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
            content_analyzer.order_fields()

        content_analyzer.set_page_status("Fields", PossiblePageStatus.COMPLETE)
        content_analyzer.set_page_status("Algorithms", PossiblePageStatus.INCOMPLETE)
        content_analyzer.set_page_status("Exogenous", PossiblePageStatus.INCOMPLETE)

        if request.args.get("type") != "Ratings" and len(content_analyzer.fields_selected) == 0:
            content_analyzer.set_page_status("Algorithms", PossiblePageStatus.DISABLED)
            content_analyzer.set_page_status("Exogenous", PossiblePageStatus.DISABLED)
        else:
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

    dict_algorithms = get_ca_algorithms()

    content_analyzer.content_production_algorithms = dict_algorithms["content_production"]
    content_analyzer.preprocess_algorithms = dict_algorithms["preprocessing"]
    content_analyzer.memory_interfaces = dict_algorithms["memory_interfaces"]
    content_analyzer.exogenous_algorithms = dict_algorithms["exogenous"]

    if content_analyzer_type == "Ratings":
        new_algorithms = [alg for alg in dict_algorithms["ratings"]
                          if alg["name"] not in [al["name"] for al in content_analyzer.ratings_algorithms]]
        content_analyzer.ratings_algorithms += new_algorithms
        selected_fields = None
    else:
        selected_fields = content_analyzer.fields_selected

    return render_template('/content-analyzer/settings.html', fields=selected_fields,
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

    content_analyzer = current_project.content_analyzer[content_analyzer_type]

    return render_template('content-analyzer/exogenous.html', project=current_project,
                           content_type=content_analyzer_type, exogenous=content_analyzer.exogenous_techniques,
                           fields_list=content_analyzer.fields_list, entity_list=dbpedia_classes)


@app.route('/ca-update-exogenous', methods=['POST'])
def ca_update_exogenous():
    global current_project

    if current_project.is_first_project():
        return redirect(url_for("index"))

    if request.form:
        action = request.form["action"]
        content_type = request.form["contentType"]
        content_analyzer = current_project.content_analyzer[content_type]

        if action == "remove":
            technique_index = int(request.form["techniqueIndex"])
            content_analyzer.remove_exogenous_technique(technique_index)
        elif action == "update":
            technique_content = json.loads(request.form["techniqueContent"])
            technique_index = int(request.form["techniqueIndex"])
            content_analyzer.update_exogenous_technique(technique_index, technique_content)

        if len(content_analyzer.exogenous_techniques) > 0:
            content_analyzer.set_page_status("Exogenous", PossiblePageStatus.COMPLETE)
        else:
            content_analyzer.set_page_status("Exogenous", PossiblePageStatus.INCOMPLETE)

    return {"result": True}


@app.route('/_exogenousformcreator', methods=['POST'])
def exogenous_form_creator():
    global current_project

    content_analyzer = current_project.content_analyzer[request.json["content_type"]]
    technique_index = request.json["technique_index"]

    if technique_index == -1:
        technique = {
            "content": content_analyzer.exogenous_algorithms,
            "fields_list": [{"name": field, "value": False} for field in content_analyzer.fields_list]
        }
        technique["content"][0]["params"][1]["value"] = "Default"
        content_analyzer.add_exogenous_technique(technique)
    else:
        technique = content_analyzer.exogenous_techniques[technique_index]

    return render_template("/content-analyzer/helpers/_exogenousformcreator.html", technique=technique)


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

    return render_template("/content-analyzer/helpers/_representationformcreator.html",
                           representations=representations, fields_list=content_analyzer.fields_list)


@app.route('/ca-update-ratings-algorithms', methods=["POST"])
def ca_update_ratings_algorithms():
    global current_project

    if current_project.is_first_project():
        return redirect(url_for("index"))

    current_project.content_analyzer_ratings.selected_algorithm = request.json["selectedAlgorithm"]
    current_project.content_analyzer_ratings.ratings_algorithms = request.json["algorithms"]
    print(current_project.content_analyzer_ratings.ratings_algorithms)
    print(request.json["algorithms"])

    return ""


@app.route('/ca-update-representations', methods=['POST'])
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

    # TODO: use only .form and not .json

    if not("delete_representation" in request.form):
        delete_representation = False
        new_representations = json.loads(request.form['representations'])
    else:
        delete_representation = True
        index_representation = request.form['index_representation']
    content_type = request.form['content_type']
    field_name = request.form['field_name']

    content_analyzer = current_project.content_analyzer[content_type]
    if delete_representation:
        content_analyzer.pop_representation(field_name, int(index_representation))
    else:
        content_analyzer.set_field(field_name, new_representations)

    if content_type == "Items":
        current_project.recommender_system.field_dict = [{
            'name': name_field,
            'use': False,
            'representations': [
                {
                    'name': rep["id"],
                    'use': False
                } for rep in reps
            ]
        } for name_field, reps in content_analyzer.fields_selected.items()]

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
        items_ca = request.form["useContentItems"] if "useContentItems" in request.form else False
        current_project.recommender_system.set_path_from_ca("Items", items_ca)

        users_ca = request.form["useContentUsers"] if "useContentUsers" in request.form else False
        current_project.recommender_system.set_path_from_ca("Users", users_ca)

        ratings_ca = request.form["useContentRatings"] if "useContentRatings" in request.form else False
        current_project.recommender_system.set_path_from_ca("Ratings", ratings_ca)

        items_path = request.form["pathItems"] if "pathItems" in request.form \
            else current_project.content_analyzer_items.output_directory
        users_path = request.form["pathUsers"] if "pathUsers" in request.form \
            else current_project.content_analyzer_users.output_directory
        ratings_path = request.form["pathRatings"] if "pathRatings" in request.form \
            else current_project.content_analyzer_ratings.output_directory

        output_directory = request.form["outputDir"]

        try:
            # TODO: Users is not used in some algs, so no checks in future
            # Various checks for the paths of items, users and ratings
            if not items_ca and items_path == "" and current_project.recommender_system.items_path != "" \
                    and not is_pathname_valid(items_path):
                list_errors.append("Path to items is invalid.")
            else:
                current_project.recommender_system.items_path = items_path

            if not users_ca and users_path == "" and current_project.recommender_system.users_path != "" \
                    and not is_pathname_valid(users_path):
                list_errors.append("Path to users is invalid.")
            else:
                current_project.recommender_system.users_path = users_path

            if not ratings_ca and ratings_path == "" and current_project.recommender_system.ratings_path != ""\
                    and not is_pathname_valid(ratings_path):
                list_errors.append("Path to ratings is invalid.")
            else:
                current_project.recommender_system.ratings_path = ratings_path

            if output_directory == "" and current_project.recommender_system.output_directory != "" \
                    and not is_pathname_valid(output_directory):
                list_errors.append("Output directory is invalid.")
            else:
                current_project.recommender_system.output_directory = output_directory

            if len(list_errors) == 0:
                if not items_ca:
                    list_errors = list_errors + check_contents(items_path, "Items")
                if not users_ca:
                    list_errors = list_errors + check_contents(users_path, "Users")

                if len(list_errors) == 0:
                    current_project.recommender_system.set_page_status("Upload", PossiblePageStatus.COMPLETE)
                    current_project.recommender_system.set_page_status("Settings", PossiblePageStatus.INCOMPLETE)
                    return redirect(url_for('recsys_settings'))
        except IndexError:
            list_errors.append("There is no valid file in the items directory <br>(<b>'" + items_path + "'</b>)")
    return render_template("./recsys/upload.html", list_errors=list_errors, project=current_project)


@app.route("/recsys/settings", methods=["POST", "GET"])
def recsys_settings():
    global current_project

    if current_project.is_first_project() \
            or current_project.recommender_system.get_page_status("Settings") == PossiblePageStatus.DISABLED:
        return redirect(url_for("index"))

    # TODO: Support dat
    if current_project.recommender_system.ratings_path.endswith("csv"):
        df = pd.read_csv(current_project.recommender_system.ratings_path)
        fields_list = list(df.columns.values)
    elif current_project.recommender_system.ratings_path.endswith("json"):
        data = json.load(open(current_project.recommender_system.ratings_path, 'r', encoding="cp866"))
        fields_list = list(data[0].keys())

    if request.method == "POST":
        from_id_column = request.form["fromIdColumn"]
        to_id_column = request.form["toIdColumn"]
        score_column = request.form["scoreColumn"]
        timestamp_column = request.form["timestampColumn"]

        if [from_id_column, to_id_column, score_column] in [fields_list] and \
                (timestamp_column in [fields_list, None]):
            current_project.recommender_system.from_id_column = from_id_column
            current_project.recommender_system.to_id_column = to_id_column
            current_project.recommender_system.score_column = score_column
            current_project.recommender_system.timestamp_column = timestamp_column
        current_project.recommender_system.set_page_status("Settings", PossiblePageStatus.COMPLETE)
        current_project.recommender_system.set_page_status("Representations", PossiblePageStatus.INCOMPLETE)
        return redirect(url_for('recsys_representations'))

    return render_template("./recsys/settings-dataset.html",
                           project=current_project,
                           fields=fields_list)


@app.route("/recsys/representations", methods=['POST', 'GET'])
def recsys_representations():
    global current_project

    if current_project.is_first_project() \
            or current_project.recommender_system.get_page_status("Representations") == PossiblePageStatus.DISABLED:
        return redirect(url_for("index"))

    if current_project.recommender_system.is_path_items_from_ca():
        get_fields_and_exogenous("Items")

    if current_project.recommender_system.is_path_users_from_ca():
        get_fields_and_exogenous("Users")

    print(current_project.recommender_system.algorithms)
    return render_template("./recsys/representations.html",
                           fields_representations=current_project.recommender_system.fields_representations,
                           exogenous=current_project.recommender_system.exogenous_techniques,
                           project=current_project)


@app.route("/update-recsys-algorithm", methods=["POST"])
def update_recsys_algorithm():
    global current_project

    if request.method == "POST":
        current_project.recommender_system.algorithms = request.json["algorithms"]
        current_project.recommender_system.selected_algorithm = request.json["selectedAlgorithm"]
        current_project.recommender_system.field_dict = request.json["listFields"]

    if current_project.recommender_system.selected_algorithm != "":
        current_project.recommender_system.set_page_status("Representations", PossiblePageStatus.COMPLETE)

    return ""


@app.route("/evalmodel/upload", methods=['POST', 'GET'])
def evalmodel_upload():
    global current_project

    if current_project.is_first_project() \
            or current_project.eval_model.get_page_status("Upload") == PossiblePageStatus.DISABLED:
        return redirect(url_for("index"))

    if request.method == "POST":
        current_project.eval_model.output_directory = request.form["outputDir"]
        if "useRecsys" in request.form and request.form["useRecsys"]:
            current_project.eval_model.recsys_config = None
            current_project.eval_model.set_page_status("Upload", PossiblePageStatus.COMPLETE)
            current_project.eval_model.set_page_status("Metrics", PossiblePageStatus.INCOMPLETE)
            return redirect(url_for("evalmodel_metrics"))
        else:
            file = request.files['pathRecsys']

            if file.filename == '':
                # TODO: bisogna dare un errore
                print('Error upload')

            if file and (file.filename.endswith(".json") or file.filename.endswith(".yaml")):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

                current_project.eval_model.recsys_config = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                current_project.eval_model.set_page_status("Upload", PossiblePageStatus.COMPLETE)
                current_project.eval_model.set_page_status("Metrics", PossiblePageStatus.INCOMPLETE)
                return redirect(url_for("evalmodel_metrics"))

    return render_template("./evalmodel/upload.html", project=current_project)


@app.route("/evalmodel/metrics", methods=["POST", "GET"])
def evalmodel_metrics():
    global current_project

    if current_project.is_first_project() \
            or current_project.eval_model.get_page_status("Settings") == PossiblePageStatus.DISABLED:
        return redirect(url_for("index"))

    return render_template("./evalmodel/settings.html",
                           project=current_project)


@app.route("/update-evalmodel-algorithms", methods=["POST"])
def update_evalmodel_algorithms():
    global current_project

    if request.method == "POST":
        current_project.eval_model.algorithms = request.json["algorithms"]
        current_project.eval_model.selected_algorithms = request.json["selectedAlgorithms"]

    current_project.eval_model.set_page_status("Metrics", PossiblePageStatus.COMPLETE)

    return ""


@app.route("/logger", methods=["GET"])
def logger():
    global current_project

    return render_template("./logger.html", project=current_project)


@app.route("/get-logger", methods=["POST", "GET"])
def get_logger():
    global current_project

    try:
        log = current_project.get_current_log()
    except Exception as e:
        print(e)
    return json.dumps({"log": log})


def execute_script(module, content_type=None, params=None):
    config_file = current_project.produce_config_file(module, content_type)
    if module == "ContentAnalyzer":
        current_project.content_analyzer[content_type].check_output_directory()
        script = [{"module": "contentanalyzer", "config": config_file, "fit": {}}]
    elif module == "RecSys":
        current_project.run(current_project.recommender_system.produce_script_ratings_importer())
        time.sleep(5)
        if current_project.recommender_system.is_path_items_from_ca():
            while current_project.running:
                time.sleep(5)
            execute_script("ContentAnalyzer", "Items")
        if current_project.recommender_system.is_path_users_from_ca():
            while current_project.running:
                time.sleep(5)
            execute_script("ContentAnalyzer", "Users")
        if current_project.recommender_system.is_path_ratings_from_ca():
            while current_project.running:
                time.sleep(5)
            execute_script("ContentAnalyzer", "Ratings")
        method = "multiple_fit_predict"
        module = config_file["class"]
        config_file.pop("class")
        script = [{"module": module.lower(),
                   "output_directory": current_project.recommender_system.output_directory,
                   method: params}]
        script[0].update(config_file)
        script[0]["rating_frame"] = current_project.recommender_system.output_directory + "\\imported_ratings.csv"
        print(script)
    elif module == "EvalModel":
        script = [{"module": "evalmodel",
                   "output_directory": current_project.eval_model.output_directory,
                   "fit": params}]
        script[0].update(config_file)

    while current_project.running:
        time.sleep(5)

    current_project.run(script)


@app.route("/execute-modules", methods=["POST", "GET"])
def execute_modules():
    global current_project

    if request.method == "POST":
        current_project.full_log = ""
        execute_script(request.json["module"],
                       request.json["contentType"] if "contentType" in request.json else None,
                       request.json["params"] if "params" in request.json else None)

        return ""
    return render_template("./execute.html", project=current_project)


@app.route("/save-config-file", methods=["GET", "POST"])
def save_config_file():
    global current_project

    if current_project is not None and request.method == "POST":
        module = request.json["module"]

        content_type = request.json["contentType"] if module == "ContentAnalyzer" else None
        config_file = current_project.produce_config_file(module, content_type)
        name_file = module.lower() + "_config" if content_type is None else module.lower() + "_" + content_type.lower() + "_config"

        with open(current_project.save_path + "/" + current_project.name + "/" + name_file + ".json", "w") as outfile:
            json.dump(config_file, outfile, indent=4)

        with open(current_project.save_path + "/" + current_project.name + "/" + name_file + ".yaml", "w") as outfile:
            yaml.dump(config_file, outfile)
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
            current_project.running = False
            current_project.init_loggers()

    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run()
