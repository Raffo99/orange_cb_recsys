import { changeActiveBlock, getClassWithParameters, showToast } from "./utils-functions.js";

function getAlgorithms(divAlgortihms) {
    let listAlgs = []
    if (divAlgortihms.hasClass("div-content-metrics")) {
        $(divAlgortihms).children(".block-metrics").children(".block-metric").each(function () {
            let listParms = []

            $(this).children(".wrapper-parameters").children(".block-parameter").each(function () {
                listParms.push(getClassWithParameters($(this)));
            });

            listAlgs.push({
                "name": $(this).attr('name').replace("metrics-", ""),
                "params": listParms,
                "use": $(this).children(".metric-label").children("input").is(":checked")
            })
        });
    }
    else {
        $(divAlgortihms).children(".block-algorithms").children(".block-algorithm").each(function () {
            let listParms = []

            $(this).children(".block-parameter").each(function () {
                listParms.push(getClassWithParameters($(this)));
            });

            listAlgs.push({
                "name": $(this).attr('name').replace("algtype-", ""),
                "params": listParms
            });
        });
    }
    return listAlgs
}

function saveAlgorithms() {
    let partitioningAlgs = getAlgorithms($("#partitioning"));
    let partitioningSelected = $("#partitioning").children(".block-algorithms-selection").children(".select-algorithm").val();
    let metrics = getAlgorithms($("#metrics"));
    let methodologyAlgs = getAlgorithms($("#methodology"));
    let methodologySelected = $("#methodology").children(".block-algorithms-selection").children(".select-algorithm").val();

    console.log(metrics)

    $.ajax({
        type: 'POST',
        url: "/update-evalmodel-algorithms",
        contentType: 'application/json; charset=UTF-8',
        data: JSON.stringify({
            "algorithms": {
                "partitioning": partitioningAlgs,
                "metrics": metrics,
                "methodology": methodologyAlgs
            },
            "selectedAlgorithms": {
                "partitioning": partitioningSelected,
                "methodology": methodologySelected
            }
        })
    });

    showToast("Settings saved successfully!", 2000);
}

$(document).ready(function () {
    $("select").each(function () {
        changeActiveBlock($(this));
    });

    $("select").change(function () {
        changeActiveBlock($(this));
    });

    $("#save-form").click(function () {
        saveAlgorithms();
    });

    $("#continue-button").click(function () {
        saveAlgorithms();
        window.location.replace("/execute-modules");
    });

    $(".block-algorithm").each(function () {
        if ($(this).children().length == 0) {
            $(this).append("<label> No parameters available for this algorithm </label>")
        }
    })

    $(".close-metric").click(function () {
        $(this).parent().parent().children(".wrapper-parameters").stop().slideToggle();
        if ($(this).text() == '–') $(this).text("+");
        else $(this).text("–");
    })
});