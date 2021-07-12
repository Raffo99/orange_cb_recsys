import pandas as pd
import os
import json

from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.utils import secure_filename
from os.path import join, dirname, realpath

from orange_cb_recsys.utils.load_content import load_content_instance
from orange_cb_recsys.content_analyzer.content_representation.content import Content

from utils.content_analyzer import get_ca_algorithms
from utils.forms import allowed_file

app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'
app.config['UPLOAD_FOLDER'] = join(dirname(realpath(__file__)), 'uploads\\')

# Global vars for content_analyzer
fields = {}
content_production_algorithms = []
preprocessing_algorithms = []
memory_interfaces = []

# Global vars for recsys
recsys_content = None


@app.route('/')
def index():

    return render_template("index.html")


# Pagina per caricare il dataset (CONTENT ANALYZER)
@app.route('/content-analyzer/upload', methods=['POST', 'GET'])
def ca_upload():
    if request.method == 'POST':
        file = request.files['pathDataset']
        if file.filename == '':
            # TODO: bisogna dare un errore
            print('Errore upload')

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            session['dirOutput'] = request.form['outputDir']
            session['pathDataset'] = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            fields.clear()
            return redirect(url_for('ca_fields'))

    return render_template('/content-analyzer/upload.html')


# Pagina per scegliere quali campi utilizzare del dataset (CONTENT ANALYZER)
@app.route('/content-analyzer/fields', methods=['POST', 'GET'])
def ca_fields():
    global fields
    if request.method == "POST":
        new_fields = dict(request.form.items(multi=False))

        for key in list(fields):
            if not(key in new_fields):
                fields.pop(key)

        for key, value in new_fields.items():
            if key == "id_dataset":
                session['id_dataset'] = value
            elif value == "on":
                if not(key in fields):
                    fields[key] = []

        # TODO: Ottimizare questa parte di codice per ordinare i campi
        temp_fields = fields.copy()
        fields.clear()
        for key in list(new_fields):
            if new_fields[key] == "on":
                fields[key] = temp_fields[key]

        return redirect(url_for('ca_settings'))

    try:
        df = pd.read_csv(session['pathDataset'])
    except:
        # TODO: Creare pagina di errore nel caso in cui pathDataset non sia settato
        return "Errore"

    return render_template('/content-analyzer/fields.html', fields=df.columns.values)


# Pagina per le varie impostazioni dei campi del dataset scelti precedentemente (CONTENT ANALYZER)
@app.route('/content-analyzer/settings', methods=['POST', 'GET'])
def ca_settings():
    global fields
    global content_production_algorithms
    global preprocessing_algorithms
    global memory_interfaces

    content_production_algorithms, preprocessing_algorithms, memory_interfaces = get_ca_algorithms()

    return render_template('/content-analyzer/settings.html', fields=fields, cp_algorithms=content_production_algorithms)


# Pagina di supporto per la creazione dei form dinamici della pagina ca-settings
@app.route('/_representationformcreator', methods=['POST'])
def representation_form_creator():
    global fields
    global content_production_algorithms
    global preprocessing_algorithms
    global memory_interfaces
    global rating_algorithms
    has_representation = request.json['has_representation']

    if has_representation:
        field_name = request.json["field_name"]
        representations = fields[field_name]

    else:
        algorithm = [a for a in content_production_algorithms if a["name"] == request.json['algorithm_name']][0]

        representations = [{
            'id': 'default',
            'algorithm': algorithm,
            'preprocess': preprocessing_algorithms,
            'values': False
        }]

    return render_template("/content-analyzer/helpers/_representationformcreator.html", representations=representations)


# Pagina di supporto per aggiornare le rappresentazioni dei campi
@app.route('/ca-update-representations', methods=['POST', 'GET'])
def ca_update_representations():
    global fields

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
        fields[field_name].pop(index_representation)
    else:
        fields[field_name] = new_representations

    return ""


@app.route("/recsys/upload", methods=['POST', 'GET'])
def recsys_upload():
    global recsys_content

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

    return render_template("./recsys/upload.html", list_errors=list_errors)


@app.route("/recsys/representations", methods=['POST', 'GET'])
def recsys_representations():
    global recsys_content

    dict_fields = recsys_content.field_dict
    for field in dict_fields.items():
        print(field[0])
        print(len(field[1].get_external_index()))
        print(field[1].get_internal_index())

    return render_template("./recsys/representations.html", fields_representations=dict_fields)


if __name__ == '__main__':
    app.run()
