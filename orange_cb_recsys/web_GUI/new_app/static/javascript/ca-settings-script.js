import { changeActiveBlock, fixName, getClassWithParameters, showToast } from "./utils-functions.js";

let $_GET = {};

if(document.location.toString().indexOf('?') !== -1) {
    var query = document.location
                   .toString()
                   // get the query string
                   .replace(/^.*?\?/, '')
                   // and remove any existing hash string (thanks, @vrijdenker)
                   .replace(/#.*$/, '')
                   .split('&');

    for(var i=0, l=query.length; i<l; i++) {
       var aux = decodeURIComponent(query[i]).split('=');
       $_GET[aux[0]] = aux[1];
    }
}

// Method used to save the current active field
function saveField() {
    let fieldName = $(".active-field").text();
    let representations = [];

    $(".div-representation").each(function () {
        let divContent = $(this).find(".div-representation-content");
        let paramsTable = divContent.children(".parameters-table");
        let nlpTable = divContent.children(".nlp-table");
        let miTable = divContent.children(".mi-table");

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

        let memory_interfaces_algorithms = []
        miTable.children(".block-algorithms").children(".block-algorithm").each(function () {
            let params_interface = []

            $(this).children(".block-parameter").each(function () {
                params_interface.push(getClassWithParameters($(this)));
            });

            memory_interfaces_algorithms.push({
                "name": $(this).attr('name').replace("algtype-", ""),
                "params": params_interface
            })
        });

        let toPush = {
            "id": idRepresentation,
            "algorithm": {
                'name': fixName($(this).find(".representation-algorithm-name").text(), true),
                'params': parameters
            }
        }

        if (nlpTechniques.length > 0) {
            toPush["preprocess"] = nlpTechniques
        }

        if (memory_interfaces_algorithms.length > 0) {
            toPush["memory_interfaces"] = {
                'algorithms': memory_interfaces_algorithms,
                'value': miTable.children(".block-algorithms-selection").children("select").val(),
                'use': miTable.children(".block-algorithms-selection").children("input[type=checkbox]").prop('checked')
            }
        }

        representations.push(toPush);
    });

    let fd = new FormData();
    fd.append('field_name', fieldName);
    fd.append('content_type', $_GET["type"])
    fd.append('representations', JSON.stringify(representations));

    navigator.sendBeacon("/ca-update-representations", fd);
}

// Method used to load a new field in the div
function loadField(nameField, listToAppend) {
    $.ajax({
        type: 'POST',
        url: "/_representationformcreator",
        contentType: 'application/json; charset=UTF-8',
        data: JSON.stringify({
            'content_type': $_GET["type"],
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

// On unload of the window, save the current active field
$(window).on("beforeunload", function () {
    saveField();
});

$("#save-form").click(function () {
    saveField();
    showToast("Fields saved successfully!", 2000);
});

// Main function for document (JQuery)
$(document).ready(function () {
    $("#continue-button").click(function () {
       saveField();

       window.location.replace("/content-analyzer/exogenous?type=" + $_GET["type"]);
    });

    $("#new-representation-options").width($("#new-representation").width() + 20);

    $(window).resize(function() {
        $("#new-representation-options").width($("#new-representation").width() + 20);
    });

    $("#new-representation").click(function () {
        $("#new-representation-options").stop().slideToggle();
    });

    $("[id^='nav-option']").first().addClass('active-field');
    $(".field-container").first().addClass('active-container');

    // Load the first field
    let listToAppend = $(".representation-list");
    let nameField = $(".active-field").attr("id").replace('nav-option-', '');

    loadField(nameField, listToAppend);

    // Method use to change the current active field
    $(".wrapper-option-number").click(function () {
        saveField();

        let listToAppend = $(".representation-list");
        let nextFieldName = $(this).find("[id^='nav-option']").text();

        listToAppend.empty();
        loadField(nextFieldName, listToAppend);

        $("[class$='active-field']").removeClass("active-field");
        $(this).find("[id^='nav-option']").addClass("active-field");
    });

    // Method used to add a new representation to the selected field
    $("#new-representation-options").on("click", ".new-representation-option", function () {
        $("#new-representation-options").stop().slideToggle();

        let listToAppend = $(".representation-list");
        let nameField = $(".active-field").attr("id").replace('nav-option-', '');

        let numberToChange = $("#nav-option-" + nameField).parent().find(".number-representations");
        numberToChange.text((numberToChange.text() * 1) + 1);
        numberToChange.addClass("active-number");

        $.ajax({
            type: 'POST',
            url: "/_representationformcreator",
            contentType: 'application/json; charset=UTF-8',
            data: JSON.stringify({
                'content_type': $_GET["type"],
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

    // Method for toggle the representations
    $(".representation-list").on("click", ".close-representation", function () {
        $(this).parent().parent().find(".wrapper-representation-content").stop().slideToggle();
        if ($(this).text() == '–') $(this).text("+");
        else $(this).text("–");
    });

    let selectedRepresentation;
    // Method used to delete a representation
    $(".representation-list").on("click", ".delete-representation", function () {
        selectedRepresentation = $(this);

        let dialogOverlay = $("#overlay").children("#dialog");

        dialogOverlay.children("#dialog-question").text("Are you sure you want to delete this representation?");

        dialogOverlay.children("#dialog-buttons").children("#dialog-yes").unbind("click");
        dialogOverlay.children("#dialog-buttons").children("#dialog-yes").click(yesDelete);

        dialogOverlay.children("#dialog-buttons").children("#dialog-no").unbind("click");
        dialogOverlay.children("#dialog-buttons").children("#dialog-no").click(function () {
            $("#overlay").fadeOut();
        });

        $("#overlay").fadeIn();
        $("#overlay").css("display", "flex");
    });

    // Method used for the yes button on the overlay (for deleting representation)
    function yesDelete() {
        $("#overlay").fadeOut();
        saveField();

        let indexRepresentation = selectedRepresentation.parent().parent().index();
        let fieldName = $(".active-field").attr("id").replace('nav-option-', '');

        let fd = new FormData();
        fd.append('field_name', fieldName);
        fd.append('content_type', $_GET["type"]);
        fd.append('delete_representation', true);
        fd.append('index_representation', indexRepresentation);

        navigator.sendBeacon("/ca-update-representations", fd);

        selectedRepresentation.parent().parent().slideToggle(function () {
            $(this).remove();
            let numberToChange = $(".active-field").parent().find(".number-representations");
            numberToChange.text((numberToChange.text() * 1) - 1);
        });
    }

    // Methods for the select list
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

    $(".representation-list").on("click", ".select-algorithm", function () {
        $(this).change(function () {
            changeActiveBlock($(this));
        });
    });

    $(".representation-list").on("click", ".add-kwargs-button", function () {
        $(this).parent().parent().children(".list-kwargs").append(
            "<div class='item-kwargs'>Name<input type='text' class='nameArg'>Value<input type='text' class='valueArg'><img class='delete-arg' src='../../static/icons/delete-icon.svg'></div>"
        );
    });

    $(".representation-list").on("click", ".delete-arg", function() {
        $(this).parent().slideToggle(function() {
            $(this).remove();
        });
    });
});