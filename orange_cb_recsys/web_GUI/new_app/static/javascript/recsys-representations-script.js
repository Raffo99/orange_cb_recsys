import { changeActiveBlock, getClassWithParameters, showToast } from "./utils-functions.js";

function saveAlgorithms() {
    let listAlgorithms = []

    $(".block-algorithm").each(function () {
        let listParameters = []

        $(this).children(".block-parameter").each(function () {
            listParameters.push(getClassWithParameters($(this)));
        });

        listAlgorithms.push({
            "name": $(this).attr('name').replace("algtype-", ""),
            "params": listParameters
        });
    })

    let selectedAlgorithm = $(".select-algorithm").val();

    let listFields = []
    if (selectedAlgorithm == "ContentBasedRS") {
        $(".field-wrapper").each(function () {
            let fieldRepresentations = []
            let fieldName = $(this).children(".field-name").text();

            $(this).children(".representations-list").children(".representation-item").each(function () {
               let representationName = $(this).children(".representation-label").text().trim();

               fieldRepresentations.push({
                   "name": representationName,
                   "use": $(this).children("input").prop("checked")
               });
            });

            listFields.push({
                "name": fieldName,
                "use": $(this).children(".field-name").children("input").prop("checked"),
                "representations": fieldRepresentations
            })
        });
    }

    $.ajax({
        type: 'POST',
        url: "/update-recsys-algorithm",
        contentType: 'application/json; charset=UTF-8',
        data: JSON.stringify({
            "algorithms": listAlgorithms,
            "selectedAlgorithm": selectedAlgorithm,
            "listFields": listFields
        })
    });

    showToast("Algorithm saved successfully!", 2000);
}

$(document).ready(function () {
    $(".add-kwargs-button").click(function () {
       $(this).parent().parent().children(".list-kwargs").append(
        "<div class='item-kwargs'>Name<input type='text' class='nameArg'>Value<input type='text' class='valueArg'><img class='delete-arg' src='../../static/icons/delete-icon.svg'></div>"
       );
    });

    $(".list-kwargs").on("click", ".delete-arg", function() {
        $(this).parent().slideToggle(function() {
            $(this).remove();
        });
    });

    $("#continue-button").click(function () {
       saveAlgorithms();
       // Redirect to next section
    });

    $("#save-form").click(function () {
        saveAlgorithms();
    });

    if ($(".select-algorithm").val() == "GraphBasedRS") {
        $(".header-representations").css("display", "none");
        $(".div-content-representations").css("display", "none");
        $(".col-6").removeClass("col-6").addClass("col-8");
    }

    $("select").each(function () {
        changeActiveBlock($(this));
    });

    $("select").change(function () {
        if ($(this).val() == "ContentBasedRS") {
            $(".col-8").removeClass("col-8").addClass("col-6");
            $(".header-representations").stop().slideToggle(function () {
                $(".div-content-representations").stop().slideToggle();
            });
        } else if ($(this).val() == "GraphBasedRS") {
            $(".div-content-representations").stop().slideToggle(function () {
                $(".header-representations").stop().slideToggle(function () {
                      $(".col-6").removeClass("col-6").addClass("col-8");
                });
            });
        }
        changeActiveBlock($(this));
    });
});

