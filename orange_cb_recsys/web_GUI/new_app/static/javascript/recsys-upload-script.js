window.onload = function() {
    $("input[type='text']").each(function () {
        let value = sessionStorage.getItem("recsys_upload_" + $(this).attr('id'));
        $(this).val(value);
    });
}

window.onunload = function()  {
    $("input[type='text']").each(function () {
        sessionStorage.setItem("recsys_upload_" + $(this).attr('id'), $(this).val());
    });

}
