function fixName(name, isAlgorithmName) {
    return (isAlgorithmName ? name.trim().replace("\n", "").replace(" ", "_") :
        name.trim().replace("\n", "").replace(" ", "_").toLowerCase());
}

// Funzione per salvare le rappresentazioni del campo selezionato
function saveField() {
    let fieldName = $(".active-field").text();
    let representations = [];

    $(".div-representation").each(function () {
        let divContent = $(this).find(".div-representation-content");
        let paramsTable = divContent.children(".hyperparam-table");
        let nlpTable = divContent.children(".nlp-table");

        let params = [];
        let nlpTechniques = [];
        let idRepresentation = $(this).find(".input-name-id").val();
        const types = {
            "text": "str",
            "number": "int",
            "checkbox": "bool"
        }

        // TODO: Supportare più tipi di campi
        let key, val, type;
        paramsTable.find("[class='table-row']").each(function () {
            $(this).find("select").each(function () {
                if (!$(this).hasClass('select-multiparam')) {
                    key = $(this).attr('name');
                    val = $(this).val();
                    type = "options"

                    params.push({
                        'name': fixName(key, false),
                        'value': val,
                        'type': type
                    })
                }
            });

            $(this).find("input").each(function () {
                if($(this).attr('type') == 'checkbox') val = $(this).prop('checked');
                else val = $(this).val();

                key = $(this).attr('name');
                type = types[$(this).attr('type')];

                params.push({
                    'name': fixName(key, false),
                    'value': val,
                    'type': type
                })
            });
        });

        let multiParamName, multiParamValue, multiParamArray = [];
        paramsTable.find(".select-multiparam").each(function () {
            multiParamName  = $(this).attr('name');
            multiParamValue = $(this).val();
            multiParamArray = []
            $(this).find("option").each(function () {
                let optionName = $(this).val();

                let paramsMultiParam = []
                paramsTable.find("[class*='" + optionName + "-" + multiParamName + "']").each(function () {
                    let nameInput = $(this).find("input").attr('name');
                    let valueInput = $(this).find("input").val();
                    let typeInput = $(this).find("input").attr('type');

                    if (optionName == multiParamValue) {
                        paramsMultiParam.push({
                            'name': nameInput,
                            'value': valueInput,
                            'type': types[typeInput]
                        });
                    } else {
                        paramsMultiParam.push({
                            'name': nameInput,
                            'type': types[typeInput]
                        });
                    }
                });

                multiParamArray.push({
                    'name': optionName,
                    'params': paramsMultiParam
                });
            });

            params.push({
                'name': multiParamName,
                'type': 'Union',
                'value': multiParamValue,
                'params': multiParamArray,
            });
        });

        let nameParam, valueParam, nlpParams;
        nlpTable.find(".nlp-technique").each(function () {
            key = $(this).find(".row-header-nlp").find("b").text();
            val = $(this).find(".row-header-nlp").find(".table-cell:first-child").find("input").prop("checked")

            nlpParams = [];

            $(this).find("[class='table-row']").each(function () {
                // TODO: Bisogna prendere gli input senza sapere che siano sempre bool
                valueParam = $(this).find(".table-cell:first-child").find("input").prop("checked");
                nameParam  = $(this).find(".table-cell:last-child").text();

                nlpParams.push({
                    'name': fixName(nameParam, false),
                    'value': valueParam,
                    'type': 'bool'
                });
            });

            nlpTechniques.push({
                'name': fixName(key, true),
                'params': nlpParams,
                'use': val
            });

        });

        console.log(params)

        let paramsTemp = params
        params = []
        $(paramsTable).find("label").each(function () {
            let orderParam = paramsTemp.filter(a => a['name'] == $(this).text());
            if (orderParam.length != 0)
                params.push(orderParam[0]);
        });

        representations.push({
            "id": idRepresentation,
            "algorithm": {
                'name': fixName($(this).find(".representation-algorithm-name").text(), true),
                'params': params
            },
            'preprocess': nlpTechniques
        });
    });

    //console.log(representations);
    let fd = new FormData();
    fd.append('field_name', fieldName);
    fd.append('representations', JSON.stringify(representations));
    console.log(representations);

    navigator.sendBeacon("/ca-update-representations", fd);
}

function loadField(nameField, listToAppend) {
    $.ajax({
        type: 'POST',
        url: "/_representationformcreator",
        contentType: 'application/json; charset=UTF-8',
        data: JSON.stringify({
            'field_name': nameField,
            'has_representation': true
        }),
        success: function (data) {
            listToAppend.append(data);
            $("[class*='active-multiparam-']").fadeIn();
            $("[class*='active-multiparam-']").css("display", "table-row");
        },
        error: function (jqXhr, textStatus, errorMessage) {
            console.log(errorMessage);
        }
    });
}

// Salvaggio del campo attuale quando si esce dalla pagina
$(window).on("unload", function () {
    saveField();
});

$(document).ready(function () {
    $("[id^='nav-option']").first().addClass('active-field');
    $(".field-container").first().addClass('active-container');

    // Caricamento del primo campo selezionato
    let listToAppend = $(".representation-list");
    let nameField = $(".active-field").attr("id").replace('nav-option-', '');

    loadField(nameField, listToAppend);

    // Funzione per cambiare da un campo all'altro, salvare i dati e caricare l'altro campo
    $(".wrapper-option-number").click(function () {
        saveField();

        let listToAppend = $(".representation-list");
        let nextFieldName = $(this).find("[id^='nav-option']").text();

        listToAppend.empty();

        loadField(nextFieldName, listToAppend);

        $("[class$='active-field']").removeClass("active-field");
        $(this).find("[id^='nav-option']").addClass("active-field");
    });

    // Funzione per aggiungere una nuova rappresentazione
    $(".select-representation").change(function () {
        let listToAppend = $(this).parent().find(".representation-list");
        let nameField = $(".active-field").attr("id").replace('nav-option-', '');

        let numberToChange = $("#nav-option-" + nameField).parent().find(".number-representations");
        numberToChange.text((numberToChange.text() * 1) + 1);
        numberToChange.addClass("active-number");

        $.ajax({
            type: 'POST',
            url: "/_representationformcreator",
            contentType: 'application/json; charset=UTF-8',
            data: JSON.stringify({
                'algorithm_name': $(this).val(),
                'has_representation': false
            }),
            success: function (data) {
                listToAppend.append(data);
                $("[class*='active-multiparam-']").fadeIn();
                $("[class*='active-multiparam-']").css("display", "table-row");
            },
            error: function (jqXhr, textStatus, errorMessage) {
                console.log(errorMessage);
            }
        });

        $(this).val("default_option");
    });

    // Funzione per chiudere e aprire le rappresentazioni
    $(".representation-list").on("click", ".close-representation", function () {
        $(this).parent().parent().find(".wrapper-representation-content").stop().slideToggle();
        if ($(this).text() == '–') $(this).text("+");
        else $(this).text("–");
    });

    // Funzione per cancellare una rappresentazione
    $(".representation-list").on("click", ".delete-representation", function () {
        saveField();

        let indexRepresentation = $(this).parent().parent().index();
        let fieldName = $(".active-field").attr("id").replace('nav-option-', '');

        $.ajax({
            type: 'POST',
            url: "/ca-update-representations",
            contentType: 'application/json; charset=UTF-8',
            data: JSON.stringify({
                'delete_representation': true,
                'field_name': fieldName,
                'index_representation': indexRepresentation
            }),
            error: function (jqXhr, textStatus, errorMessage) {
                console.log(errorMessage);
            }
        });

        $(this).parent().parent().remove();
        let numberToChange = $(".active-field").parent().find(".number-representations");
        numberToChange.text((numberToChange.text() * 1) - 1)
    });

    // Funzione per i parametri con valori complessi
    $(".representation-list").on("click", ".select-multiparam", function() {
        $(this).change(function () {
            let nameToActive = $(this).find('option:selected').attr('value').replace(" ", "");
            let nameParam = $(this).attr('name');
            let toRemove = $(this).parent().parent().parent().find(".active-multiparam-" + nameParam);
            let toAdd = $(this).parent().parent().parent().find("." + nameToActive + "-" + nameParam);

            toRemove.css("display", "");
            toRemove.removeClass("active-multiparam-" + nameParam);
            toAdd.addClass('active-multiparam-' + nameParam);
            toAdd.fadeIn();
            toAdd.css("display", "table-row");
        });
    });
});