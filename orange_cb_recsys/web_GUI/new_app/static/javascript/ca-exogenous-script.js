import { changeActiveBlock, getClassWithParameters, showToast} from "./utils-functions.js";
let $_GET = {};
const new_technique = -1;

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

function adjustTables() {
    if ($(".select-subclass[name='exogenous_technique']").val() == "PropertiesFromDataset") {
        $(".col-6").removeClass("col-6").addClass("col-4");
        $(".header-fields").stop().slideDown(function () {
            $(".div-content-fields").stop().slideDown();
        });
    } else {
        $(".div-content-fields").stop().slideUp(function () {
            $(".header-fields").stop().slideUp(function () {
                $(".col-4").removeClass("col-4").addClass("col-6");
            });
        });
    }
}

function updateComponents() {
    $(".select-union").each(function () {
        changeActiveBlock($(this));
        adjustTables();
    });

    $(".select-subclass").each(function () {
        changeActiveBlock($(this));
        adjustTables();
    });

    $(".select-algorithm").each(function () {
        changeActiveBlock($(this));
        adjustTables();
    });

    $(".select-union").change(function() {
       changeActiveBlock($(this));
       adjustTables();
    });

    $(".select-subclass").change(function () {
        changeActiveBlock($(this));
        adjustTables();
    });

    $(".select-algorithm").change(function () {
        changeActiveBlock($(this));
        adjustTables();
    });

    $("input[name='entity_type']").autocomplete({
        source: entityList
    });

    $("input[name='id']").keyup(function () {
        if ($(this).val() == "") {
            $(this).val("Default");
            showToast("Exogenous name can't be empty!", 2000);
        }

        $(".active-technique").children("label").text($(this).val());
    });
}

function saveTechnique() {
    let fd = new FormData();

    if (!$(".active-technique")[0]) return
    let indexTechnique = $(".active-technique").index();
    fd.append('techniqueIndex', indexTechnique);

    let parameters = []
    $(".div-exogenous").children("[class='block-parameter']").each(function () {
        parameters.push(getClassWithParameters($(this)));
    });

    let fieldsList = []
    $(".div-content-fields").children(".field-wrapper").each(function () {
        fieldsList.push({
            'name': $(this).children(".field-name").children("label").text(),
            'value': $(this).children(".field-name").children("input").is(":checked")
        })
    });

    let exogenousTechnique = {
        "content": [{
            "name": "ExogenousConfig",
            "params": parameters
        }],
        "fields_list": fieldsList
    }

    fd.append('action', "update");
    fd.append('contentType', $_GET["type"]);
    fd.append('techniqueContent', JSON.stringify(exogenousTechnique));

    navigator.sendBeacon("/ca-update-exogenous", fd);
}

function deleteTechnique(event) {
    let indexTechnique = event.data.index;

    if ($(".active-technique")[0]) {
        saveTechnique();
        if ($(".active-technique").index() == indexTechnique) {
            $(".technique").eq(0).children("label").trigger("click");
        }
    }

    let fd = new FormData();

    fd.append('action', "remove");
    fd.append('contentType', $_GET["type"])
    fd.append('techniqueIndex', indexTechnique);

    navigator.sendBeacon("/ca-update-exogenous", fd);
    $("#overlay").fadeOut();

    $(".technique").eq(indexTechnique).slideToggle(function () {
        $(this).remove();
    });
}

function clearTechnique() {
    $(".div-exogenous").children().each(function () {
        $(this).remove();
    });

    $(".div-content-fields").children().each(function () {
        $(this).remove();
    });
}

function loadTechnique(technique_index) {
    $.ajax({
        type: 'POST',
        url: "/_exogenousformcreator",
        contentType: 'application/json; charset=UTF-8',
        data: JSON.stringify({
            "content_type": $_GET["type"],
            "technique_index": technique_index
        }),
        success: function (data) {
            let fieldIndex = data.indexOf("\"fields_list\"");

            data = data.substring(0, 28) + (data.substring(28, fieldIndex).replaceAll("\"", "\\\""))
             + data.substring(fieldIndex, fieldIndex + "\"fields_list\": '".length)
             + data.substring(fieldIndex + "\"fields_list\": '".length).replaceAll("\"", "\\\"");

            data = data.replaceAll("'", "\"").replaceAll("\n", "");

            let json_data = JSON.parse(data);
            clearTechnique();

            $(".div-exogenous").append(json_data["exogenous_div"])
            $(".div-content-fields").append(json_data["fields_list"])

            updateComponents();
            adjustTables();
        },
        error: function (jqXhr, textStatus, errorMessage) {
            console.log(errorMessage);
        }
    });
}

$(".button-new-technique").click(function () {
    if ($(".active-technique")[0]) {
        saveTechnique();
        clearTechnique();
        $(".active-technique").removeClass("active-technique");
    }

    loadTechnique(new_technique);
    $("#list-techniques").append("<div class='technique active-technique'><label>Default</label><img class='delete-exo' src='../../static/icons/delete-icon.svg'></div>");
    $("#list-techniques").animate({ scrollTop: $("#list-techniques").prop('scrollHeight')}, 1);
});

$(document).ready(function() {
    $("#continue-button").click(function () {
        saveTechnique();
        let location = "/recsys/upload"
        if ($_GET["type"] == "Items") location = "/content-analyzer/upload?type=Users";
        else if ($_GET["type"] == "Users") location = "/content-analyzer/upload?type=Ratings";
        window.location.replace(location);
    });

    $("#list-techniques").on("click", ".technique label", function () {
        if ($(".active-technique")[0]) {
            saveTechnique();
            $(".active-technique").removeClass("active-technique");
        }

        loadTechnique($(this).parent().index());
        $(this).parent().addClass("active-technique");
    });

    $("#list-techniques").on("click", ".delete-exo", function () {
        let indexTechnique = $(this).parent().index();
        let dialogOverlay = $("#overlay").children("#dialog");

        dialogOverlay.children("#dialog-question").text("Are you sure you want to delete this exogenous?");

        dialogOverlay.children("#dialog-buttons").children("#dialog-yes").unbind("click");
        dialogOverlay.children("#dialog-buttons").children("#dialog-yes").click({"index": indexTechnique}, deleteTechnique);

        dialogOverlay.children("#dialog-buttons").children("#dialog-no").unbind("click");
        dialogOverlay.children("#dialog-buttons").children("#dialog-no").click(function () {
            $("#overlay").fadeOut();
        });

        $("#overlay").fadeIn();
        $("#overlay").css("display", "flex");
    });

    $(window).on("beforeunload", function () {
        saveTechnique();
    });

})
