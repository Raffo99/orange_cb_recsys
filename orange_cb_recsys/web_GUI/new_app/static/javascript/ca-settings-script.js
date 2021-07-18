import { changeActiveBlock } from "./utils-functions.js";
import { fixName } from "./utils-functions.js";

function getClassWithParameters(blockParameter) {
    const types = {
        "text": "str",
        "number": "int",
        "checkbox": "bool"
    }

    if (blockParameter.children("[class='block-union-selection']").length > 0) {
        // Parameter is Union
        let parameters = [];
        blockParameter.children("[class='block-union-parameter']").children("[class*='block-parameter']").each(function () {
            parameters.push(getClassWithParameters($(this)));
        });

        blockParameter.children("[class='block-union-selection']").children("select").children("option").each(function (index) {
            parameters[index]["name"] = $(this).val();
        });

        return {
            'name': blockParameter.children("[class='block-union-selection']").children("label").text(),
            'type': 'Union',
            'value': blockParameter.children("[class='block-union-selection']").children("select").val(),
            'params': parameters
        }
    } else {
        let blockParameterContainer = (blockParameter.children("[class*='block-parameter-container']"));

        if (blockParameterContainer.children("[class*='block-sub-classes']").length > 0) {
            // Parameter is Complex with sub classes
            let subClasses = [];
            let blockSubClasses = blockParameterContainer.children("[class='block-sub-classes']");
            blockSubClasses.children("[class*='block-parameter']").each(function () {
                subClasses.push(getClassWithParameters($(this)));
            });

            blockParameterContainer.children("[class='block-sub-classes-selection']").children("select").children("option").each(function (index) {
               subClasses[index]["name"] = $(this).val();
            });

            return {
                'name': blockParameterContainer.children("[class='block-sub-classes-selection']").children("label").text(),
                'type': 'Complex',
                'value': blockParameterContainer.children("[class='block-sub-classes-selection']").children("select").val(),
                'sub_classes': subClasses
            }
        } else if (blockParameterContainer.children("[class='block-parameter']").length > 0) {
            // Parameter is Complex with parameters
            let parameters = [];
            blockParameterContainer.children("[class*='block-parameter']").each(function () {
                parameters.push(getClassWithParameters($(this)));
            });

            return {
                'name': blockParameterContainer.children("label").text(),
                'type': 'Complex',
                'params': parameters
            }
        } else {
            let value = blockParameterContainer.children("input").attr("type") == "checkbox" ?
                blockParameterContainer.children("input").is(":checked") :
                blockParameterContainer.children("input").val();
            // Parameter is Simple
            return {
                'name': blockParameterContainer.children("label").text(),
                'type': types[blockParameterContainer.children("input").attr('type')],
                'value': value
            }
        }
    }
}

// Funzione per salvare le rappresentazioni del campo selezionato
function saveField() {
    let fieldName = $(".active-field").text();
    let representations = [];

    $(".div-representation").each(function () {
        let divContent = $(this).find(".div-representation-content");
        let paramsTable = divContent.children(".parameters-table");
        let nlpTable = divContent.children(".nlp-table");

        let idRepresentation = $(this).find(".input-name-id").val();

        let parameters = [];
        let nlpTechniques = [];
        paramsTable.children("[class='block-parameter']").each(function () {
            parameters.push(getClassWithParameters($(this)));
        });

        nlpTable.children(".nlp-technique").each(function () {
            let nlpParams = [];
            $(this).children(".block-parameter").each(function () {
               nlpParams.push(getClassWithParameters($(this)));
            });

            nlpTechniques.push({
                'name': $(this).children(".nlp-name").children("label").text(),
                'use': $(this).children(".nlp-name").children("input").is(":checked"),
                'params': nlpParams
            })
        });

        representations.push({
            "id": idRepresentation,
            "algorithm": {
                'name': fixName($(this).find(".representation-algorithm-name").text(), true),
                'params': parameters
            },
            'preprocess': nlpTechniques
        });
    });

    let fd = new FormData();
    fd.append('field_name', fieldName);
    fd.append('representations', JSON.stringify(representations));

    navigator.sendBeacon("/ca-update-representations", fd);
    console.log("Inviato");
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
            $("[class*='active-block']").fadeIn();
            $("[class*='active-block']").css("display", "block");
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
    $("#new-representation-options").width($("#new-representation").width() + 20);

    $(window).resize(function() {
        $("#new-representation-options").width($("#new-representation").width() + 20);
    });

    $("#new-representation").click(function () {
        $("#new-representation-options").stop().slideToggle();
    });

    $("[id^='nav-option']").first().addClass('active-field');
    $(".field-container").first().addClass('active-container');

    // Caricamento del primo campo selezionato
    let listToAppend = $(".representation-list");
    let nameField = $(".active-field").attr("id").replace('nav-option-', '');

    loadField(nameField, listToAppend);

    // Funzione per cambiare da un campo all'altro, salvare i dati e caricare l'altro campo
    $(".wrapper-option-number").click(function () {
        saveField();
        console.log("Finito")

        let listToAppend = $(".representation-list");
        let nextFieldName = $(this).find("[id^='nav-option']").text();

        listToAppend.empty();
        loadField(nextFieldName, listToAppend);

        $("[class$='active-field']").removeClass("active-field");
        $(this).find("[id^='nav-option']").addClass("active-field");
    });

    // Funzione per aggiungere una nuova rappresentazione
    $("#new-representation-options").on("click", ".new-representation-option", function () {
        $("#new-representation-options").stop().slideToggle();

        let listToAppend = $(".representation-list");
        let nameField = $(".active-field").attr("id").replace('nav-option-', '');

        let numberToChange = $("#nav-option-" + nameField).parent().find(".number-representations");
        numberToChange.text((numberToChange.text() * 1) + 1);
        numberToChange.addClass("active-number");
        console.log($(this).find("label").text());

        $.ajax({
            type: 'POST',
            url: "/_representationformcreator",
            contentType: 'application/json; charset=UTF-8',
            data: JSON.stringify({
                'algorithm_name': $(this).find("label").text(),
                'has_representation': false
            }),
            success: function (data) {
                listToAppend.append(data);
                $("[class*='active-block']").fadeIn();
                $("[class*='active-block-']").css("display", "block");
            },
            error: function (jqXhr, textStatus, errorMessage) {
                console.log(errorMessage);
            }
        });
    });

    // Funzione per chiudere e aprire le rappresentazioni
    $(".representation-list").on("click", ".close-representation", function () {
        $(this).parent().parent().find(".wrapper-representation-content").stop().slideToggle();
        if ($(this).text() == '–') $(this).text("+");
        else $(this).text("–");
    });

    let selectedRepresentation;
    // Funzione per cancellare una rappresentazione
    $(".representation-list").on("click", ".delete-representation", function () {
        $("#overlay").fadeIn();
        $("#overlay").css("display", "flex");
        selectedRepresentation = $(this);
    });

    $("#dialog-no").click(function () {
        $("#overlay").fadeOut();
    });

    $("#dialog-yes").click(function () {
        $("#overlay").fadeOut();
        saveField();

        let indexRepresentation = selectedRepresentation.parent().parent().index();
        console.log(indexRepresentation)
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

        selectedRepresentation.parent().parent().slideToggle(function () {
            $(this).remove();
            let numberToChange = $(".active-field").parent().find(".number-representations");
            numberToChange.text((numberToChange.text() * 1) - 1);
        });
    });

    // Funzione per i parametri con valori complessi
    $(".representation-list").on("click", ".select-union", function() {
        $(this).change(function () {
            changeActiveBlock($(this));
        });
    });

    $(".representation-list").on("click", ".select-subclass", function () {
        $(this).change(function () {
            changeActiveBlock($(this));
        });
    })
});