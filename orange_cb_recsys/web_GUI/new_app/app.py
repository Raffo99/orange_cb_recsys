import importlib

from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from werkzeug.utils import secure_filename
import pandas as pd
import os
from os.path import join, dirname, realpath
import json

from orange_cb_recsys.utils.load_content import load_content_instance
from orange_cb_recsys.content_analyzer.content_representation.content import Content
# import orange_cb_recsys.utils.runnable_instances as r_i
from inspect import signature
import inspect


app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'
app.config['UPLOAD_FOLDER'] = join(dirname(realpath(__file__)), 'uploads\\')

# Global vars for content_analyzer
ALLOWED_EXTENSIONS = {'csv', 'json', 'dat'}
fields = {}
# instances_categories = r_i.categories
# runnable_instances = r_i.get()
content_production_algorithms = []
preprocessing_algorithms = []
memory_interfaces = []
rating_algorithms = []

# Global vars for recsys
recsys_content = None


# TODO: Add to a util gui module
def update_ca_algorithms():
    global content_production_algorithms
    global preprocessing_algorithms
    global memory_interfaces
    global rating_algorithms

    content_production_algorithms = []
    preprocessing_algorithms = []
    memory_interfaces = []
    rating_algorithms = []

    content_production_instances = []
    preprocessing_instances = []
    rating_instances = []
    memory_interface_instances = []

    '''
    for instance in runnable_instances.items():
        if not(isinstance(instance[1], str)) \
                and "content_analyzer" in instance[1].__module__\
                and not ("raw_information_source" in instance[1].__module__):
            module_path = instance[1].__module__
            if "memory_interface" in module_path:
                memory_interface_instances.append(instance)
            elif "information_processor" in module_path:
                preprocessing_instances.append(instance)
            elif "field_content_production_techniques" in module_path:
                if len([a for a in instance[1].__mro__ if a.__name__ == "FieldContentProductionTechnique"]):
                    content_production_instances.append(instance)
            elif "ratings_manager" in module_path:
                rating_instances.append(instance)
    '''

    # Get all the algorithms from the runnable instances
    add_algorithms(content_production_algorithms, content_production_instances)
    add_algorithms(preprocessing_algorithms, preprocessing_instances)
    add_algorithms(rating_algorithms, rating_instances)


# TODO: Add to a util gui module
def get_parameters(signature_parameters):
    if "self" in signature_parameters:
        signature_parameters.remove("self")
    parameters_array = []

    for parm in signature_parameters:
        if parm[1].name != 'lang':
            parm_class = parm[1].annotation.__name__
            if parm_class == 'bool' or parm_class == 'str' or parm_class == 'float':
                # If the parameter is a simple class, i can directly add it to the array
                parameters_array.append({
                    'name': parm[1].name,
                    'type': parm_class
                })
            else:
                # If the parameter is a complex class, i can retrieve the possible values of the parameter
                name_module = parm[1].annotation.__module__
                last_index_point = name_module.rindex(".")
                name_module = name_module[:(last_index_point - len(name_module))]
                possible_values = []

                '''
                for inst in runnable_instances.items():
                    if (not isinstance(inst[1], str)) and parm[1].annotation in inspect.getmro(inst[1]):
                        possible_values.append({
                            'name': inst[1].__name__,
                            'params': get_parameters(list(signature(inst[1]).parameters.items()))
                        })
                '''

                parameters_array.append({
                    'name': parm[1].name,
                    'type': 'radio',
                    'params': possible_values
                })
    return parameters_array


# TODO: Add to a util gui module
def add_algorithms(algorithms_array, instances_array):

    for instance in instances_array:
        signature_parameters = list(signature(instance[1]).parameters.items())

        # Get all the parameter of the instance
        parameters_array = get_parameters(signature_parameters)

        algorithms_array.append({
            'name': instance[1].__name__,
            'params': parameters_array
        })


# TODO: Add to a util gui module
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    update_ca_algorithms()
    return render_template("index.html")


# Pagina per caricare il dataset (CONTENT ANALYZER)
@app.route('/ca-upload', methods=['POST', 'GET'])
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

    return render_template('ca-upload.html')


# Pagina per scegliere quali campi utilizzare del dataset (CONTENT ANALYZER)
@app.route('/ca-fields', methods=['POST', 'GET'])
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

    return render_template('ca-fields.html', fields=df.columns.values)


# Pagina per le varie impostazioni dei campi del dataset scelti precedentemente (CONTENT ANALYZER)
@app.route('/ca-settings', methods=['POST', 'GET'])
def ca_settings():
    global fields
    global content_production_algorithms
    global preprocessing_algorithms
    global memory_interfaces
    global rating_algorithms

    update_ca_algorithms()

    return render_template('ca-settings.html', fields=fields, cp_algorithms=content_production_algorithms)


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

    return render_template("_representationformcreator.html", representations=representations)


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
