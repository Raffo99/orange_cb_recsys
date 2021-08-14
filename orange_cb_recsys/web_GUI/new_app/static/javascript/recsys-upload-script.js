$(document).ready(function () {
    $("#useContentItems").click(function () {
        $("#pathItems").prop("disabled", $(this).is(":checked"));
    });

    $("useContentUsers").click(function () {
        $("#pathUsers").prop("disabled", $(this).is(":checked"));
    });

    $("useContentRatings").click(function () {
        $("#pathRatings").prop("disabled", $(this).is(":checked"));
    });
});