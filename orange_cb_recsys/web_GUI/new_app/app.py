import pandas as pd
import os
import json

from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.utils import secure_filename
from os.path import join, dirname, realpath

from orange_cb_recsys.utils.load_content import load_content_instance
from orange_cb_recsys.content_analyzer.content_representation.content import Content

from utils.algorithms import get_ca_algorithms
from utils.algorithms import get_recsys_algorithms
from utils.forms import allowed_file

from project import Project, ContentAnalyzerModule, PossiblePageStatus

app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'
app.config['UPLOAD_FOLDER'] = join(dirname(realpath(__file__)), 'uploads\\')

# Global vars for content_analyzer
current_project = Project()

# Global vars for recsys
recsys_content = None


@app.route('/')
def index():
    return render_template("index.html")


# Pagina per caricare il dataset (CONTENT ANALYZER)
@app.route('/content-analyzer/upload', methods=['POST', 'GET'])
def ca_upload():
    global current_project

    if request.method == 'POST':
        file = request.files['pathDataset']
        if file.filename == '':
            # TODO: bisogna dare un errore
            print('Errore upload')

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            current_project.content_analyzer.set_output_directory(request.form["outputDir"])
            current_project.content_analyzer.set_source_path(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            current_project.content_analyzer.clear_fields()
            current_project.content_analyzer.clear_id_fields()

            current_project.content_analyzer.set_page_status("Upload", PossiblePageStatus.COMPLETE)
            current_project.content_analyzer.set_page_status("Fields", PossiblePageStatus.INCOMPLETE)
            current_project.content_analyzer.set_page_status("Algorithms", PossiblePageStatus.DISABLED)
            current_project.content_analyzer.set_page_status("Execute", PossiblePageStatus.DISABLED)
            return redirect(url_for('ca_fields'))
    return render_template('/content-analyzer/upload.html', project=current_project)


# Pagina per scegliere quali campi utilizzare del dataset (CONTENT ANALYZER)
@app.route('/content-analyzer/fields', methods=['POST', 'GET'])
def ca_fields():
    global current_project

    if request.method == "POST":
        new_fields = dict(request.form.items(multi=False))
        for key in list(current_project.content_analyzer.get_fields()):
            if not(key in list(map(lambda x: ContentAnalyzerModule.convert_key(x), new_fields))):
                current_project.content_analyzer.pop_field(key)

        for key, value in new_fields.items():
            if "__fieldid" in key:
                current_project.content_analyzer.add_id_field(key.replace("__fieldid", ""))
            elif not (ContentAnalyzerModule.convert_key(key) in current_project.content_analyzer.get_fields()):
                current_project.content_analyzer.set_field(key, [])

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


# Pagina per le varie impostazioni dei campi del dataset scelti precedentemente (CONTENT ANALYZER)
@app.route('/content-analyzer/algorithms', methods=['POST', 'GET'])
def ca_settings():
    global current_project

    content_production_algorithms, preprocessing_algorithms, memory_interfaces = get_ca_algorithms()
    current_project.content_analyzer.set_content_production_algorithms(content_production_algorithms)
    current_project.content_analyzer.set_preprocess_algorithms(preprocessing_algorithms)
    current_project.content_analyzer.set_memory_interfaces(memory_interfaces)

    return render_template('/content-analyzer/settings.html', fields=current_project.content_analyzer.get_fields(),
                           cp_algorithms=content_production_algorithms, project=current_project)


# Pagina di supporto per la creazione dei form dinamici della pagina ca-settings
@app.route('/_representationformcreator', methods=['POST'])
def representation_form_creator():
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


# Pagina di supporto per aggiornare le rappresentazioni dei campi
@app.route('/ca-update-representations', methods=['POST', 'GET'])
def ca_update_representations():
    global current_project

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
        print(field_name)
        print(index_representation)
        current_project.content_analyzer.pop_representation(field_name, index_representation)
    else:
        current_project.content_analyzer.set_field(field_name, new_representations)

    return ""


@app.route("/recsys/upload", methods=['POST', 'GET'])
def recsys_upload():
    global recsys_content
    global current_project

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

    algorithms = get_recsys_algorithms()

    return render_template("/recsys/representations.html", fields_representations=recsys_content.field_dict,
                           algorithms=algorithms, project=current_project)


if __name__ == '__main__':
    app.run()
