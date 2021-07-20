import pandas as pd
import os
import json
import pickle

from flask import Flask, render_template, request, redirect, url_for
from werkzeug.utils import secure_filename
from os.path import join, dirname, realpath
from pathlib import Path

from orange_cb_recsys.utils.load_content import load_content_instance
from orange_cb_recsys.content_analyzer.content_representation.content import Content

from utils.algorithms import get_ca_algorithms
from utils.algorithms import get_recsys_algorithms
from utils.forms import allowed_file, is_pathname_valid
from project import Project, ContentAnalyzerModule, PossiblePageStatus

from orange_cb_recsys.script_handling import script_run

app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'
app.config['UPLOAD_FOLDER'] = join(dirname(realpath(__file__)), 'uploads\\')
app.config["PROJECTS_FOLDER"] = join(dirname(realpath(__file__)), 'projects\\')

# Global variable for the current project
current_project = None

# TODO: use the recsys in Project
recsys_content = None


@app.route('/', methods=["POST", "GET"])
def index():
    global current_project

    if request.method == 'POST':
        current_project = Project()
        return redirect(url_for("ca_upload"))

    return render_template("index.html")


@app.route('/content-analyzer/upload', methods=['POST', 'GET'])
def ca_upload():
    """
    Page where the user can select the dataset to use in the content analyzer and the output directory.
    It can return the page of upload, or redirect to the next stage of the content analyzer if the method is POST and
    the dataset is a correct dataset.
    """
    global current_project

    if current_project is None:
        return redirect(url_for("index"))

    list_errors = []

    if request.method == 'POST':
        file = request.files['pathDataset']

        if is_pathname_valid(request.form["outputDir"]):
            current_project.content_analyzer.set_output_directory(request.form["outputDir"])
        else:
            list_errors.append("Wrong output directory!")

        if file and not(allowed_file(file.filename)):
            list_errors.append("Wrong file type!")

        if file and len(list_errors) == 0:
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            current_project.content_analyzer.set_source_path(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            current_project.content_analyzer.clear_fields()
            current_project.content_analyzer.clear_id_fields()

            current_project.content_analyzer.set_page_status("Upload", PossiblePageStatus.COMPLETE)
            current_project.content_analyzer.set_page_status("Fields", PossiblePageStatus.INCOMPLETE)
            current_project.content_analyzer.set_page_status("Algorithms", PossiblePageStatus.DISABLED)
            return redirect(url_for('ca_fields'))
        elif len(list_errors) == 0 and current_project.content_analyzer.has_already_dataset():
            return redirect(url_for('ca_fields'))

    # print(current_project.content_analyzer.get_fields())
    # print(current_project.content_analyzer.produce_config_file())
    # script_run(current_project.content_analyzer.produce_config_file())

    return render_template('/content-analyzer/upload.html', project=current_project, list_errors=list_errors)


@app.route('/content-analyzer/fields', methods=['POST', 'GET'])
def ca_fields():
    """
    Page where the user can select what fields serialize from the dataset and what field is a field id.
    """
    global current_project

    if current_project is None:
        return redirect(url_for("index"))

    if request.method == "POST":
        new_fields = dict(request.form.items(multi=False))
        for key in list(current_project.content_analyzer.get_fields()):
            if not(key in list(map(lambda x: ContentAnalyzerModule.convert_key(x), new_fields))):
                current_project.content_analyzer.pop_field(key)

        temp_fields_id = []
        for key, value in new_fields.items():
            if "__fieldid" in key:
                temp_fields_id.append(key.replace("__fieldid", ""))
            elif not (ContentAnalyzerModule.convert_key(key) in current_project.content_analyzer.get_fields()):
                current_project.content_analyzer.set_field(key, [])
        current_project.content_analyzer.set_id_fields(temp_fields_id)

        if not current_project.content_analyzer.get_fields():
            # TODO: Dare errore nel caso in cui fields è vuoto
            return "ERRORE"
        else:
            current_project.content_analyzer.order_fields()

            current_project.content_analyzer.set_page_status("Fields", PossiblePageStatus.COMPLETE)
            current_project.content_analyzer.set_page_status("Algorithms", PossiblePageStatus.INCOMPLETE)
            return redirect(url_for('ca_settings'))

    try:
        # TODO: Supportare anche json e dat
        df = pd.read_csv(current_project.content_analyzer.get_source_path())
    except:
        # TODO: Dare errore nel caso in cui pathDataset non sia settato
        return "Errore"

    return render_template('/content-analyzer/fields.html', fields=df.columns.values, project=current_project)


@app.route('/content-analyzer/algorithms', methods=['POST', 'GET'])
def ca_settings():
    """
    Page where the user can select what algorithm to use for every field selected, and also what parameter to use
    for every algorithm, it NOT CHECKS the correctness of the parameters!!
    """
    global current_project

    if current_project is None:
        return redirect(url_for("index"))

    # TODO: Optimize code down there in one line
    content_production_algorithms, preprocessing_algorithms, memory_interfaces = get_ca_algorithms()

    current_project.content_analyzer.set_content_production_algorithms(content_production_algorithms)
    current_project.content_analyzer.set_preprocess_algorithms(preprocessing_algorithms)
    current_project.content_analyzer.set_memory_interfaces(memory_interfaces)

    return render_template('/content-analyzer/settings.html', fields=current_project.content_analyzer.get_fields(),
                           cp_algorithms=content_production_algorithms, project=current_project)


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

    fields = current_project.content_analyzer.get_fields()

    has_representation = request.json['has_representation']

    if has_representation:
        field_name = request.json["field_name"]
        representations = fields[field_name]
    else:
        content_production_algorithms = current_project.content_analyzer.get_content_production_algorithms()
        algorithm = [a for a in content_production_algorithms if a["name"] == request.json['algorithm_name']][0]

        representations = [{
            'id': 'default',
            'algorithm': algorithm,
            'preprocess': current_project.content_analyzer.get_preprocess_algorithms(),
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

    if current_project is None:
        return redirect(url_for("index"))

    if request.form:
        if not("delete_representation" in request.form):
            delete_representation = False
            new_representations = json.loads(request.form['representations'])
        else:
            delete_representation = True
            index_representation = request.form['index_representation']
        field_name = request.form['field_name']
    else:
        if not("delete_representation" in request.json):
            delete_representation = False
            new_representations = request.json['representations']
        else:
            delete_representation = True
            index_representation = request.json['index_representation']
        field_name = request.json['field_name']

    if delete_representation:
        current_project.content_analyzer.pop_representation(field_name, index_representation)
    else:
        current_project.content_analyzer.set_field(field_name, new_representations)

    if any(len(representation) > 0 for representation in current_project.content_analyzer.get_fields().values()):
        current_project.content_analyzer.set_page_status("Algorithms", PossiblePageStatus.COMPLETE)
    else:
        current_project.content_analyzer.set_page_status("Algorithms", PossiblePageStatus.INCOMPLETE)

    return ""


@app.route("/recsys/upload", methods=['POST', 'GET'])
def recsys_upload():
    global recsys_content
    global current_project

    if current_project is None:
        return redirect(url_for("index"))

    list_errors = []
    if request.method == 'POST':
        path_content = request.form["pathContent"]
        output_directory = request.form["outputDir"]
        try:
            if path_content == "":
                list_errors.append("Path to content is empty.")
            if output_directory == "":
                list_errors.append("Output directory is empty.")

            if len(list_errors) == 0:
                list_files = [f for f in os.listdir(path_content) if os.path.isfile(join(path_content, f)) and ".xz" in f]
                file_to_check = list_files[0]
                content = load_content_instance(path_content, file_to_check.replace(".xz", ""))
                if isinstance(content, Content):
                    recsys_content = content
                    current_project.recommender_system.set_page_status("Upload", PossiblePageStatus.COMPLETE)
                    return redirect(url_for('recsys_representations'))
                else:
                    list_errors.append("Invalid content file in content's directory <br>(<b>'" + path_content + "'</b>)")
        except IndexError:
            list_errors.append("There is no valid file in the content's directory <br>(<b>'" + path_content + "'</b>)")
        except FileNotFoundError:
            list_errors.append("<b>'" + path_content + "'</b> is not a valid directory.")
        except OSError:
            list_errors.append("Wrong syntax in path to content.")

    return render_template("./recsys/upload.html", list_errors=list_errors, project=current_project)


@app.route("/recsys/representations", methods=['POST', 'GET'])
def recsys_representations():
    global recsys_content
    global current_project

    if current_project is None:
        return redirect(url_for("index"))

    print(recsys_content)
    print(recsys_content.field_dict)
    algorithms = get_recsys_algorithms()

    return render_template("/recsys/representations.html", fields_representations=recsys_content.field_dict,
                           algorithms=algorithms, project=current_project)


@app.route("/save-current-project", methods=["GET", "POST"])
def save_current_project():
    """
    Support page used to save the variable current_project
    """
    global current_project

    if current_project is None:
        return redirect(url_for("index"))

    # TODO: Cambiare nome al progetto dall'interfaccia
    current_project.name = "test"

    # TODO: Salvare da interfaccia
    Path(app.config["PROJECTS_FOLDER"] + current_project.name + "/").mkdir(parents=True, exist_ok=True)

    with open(app.config["PROJECTS_FOLDER"] + current_project.name + "/" + current_project.name + ".prj", 'wb') as output:
        pickle.dump(current_project, output, pickle.HIGHEST_PROTOCOL)

    return ""


@app.route("/load-new-project", methods=["GET", "POST"])
def load_new_project():
    """
    Support page used to load a project file, it use the file passed in the POST request with some checks on the file
    """
    global current_project

    print(request.files)
    file = request.files['pathProject']

    if file.filename == '':
        # TODO: bisogna dare un errore
        print('Errore upload')

    if file and file.filename.endswith(".prj"):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        with open(os.path.join(app.config['UPLOAD_FOLDER'], filename), 'rb') as input_project:
            current_project = pickle.load(input_project)

    return redirect(url_for('ca_upload'))


if __name__ == '__main__':
    app.run()
