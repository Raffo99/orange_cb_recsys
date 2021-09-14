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
    console.log(listAlgorithms);

    $.ajax({
        type: 'POST',
        url: "/ca-update-ratings-algorithms",
        contentType: 'application/json; charset=UTF-8',
        data: JSON.stringify({
            "algorithms": listAlgorithms,
            "selectedAlgorithm": selectedAlgorithm
        })
    });

    showToast("Algorithm saved successfully!", 2000);
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
        showToast("Algorithm saved successfully!", 2000);
    });
});