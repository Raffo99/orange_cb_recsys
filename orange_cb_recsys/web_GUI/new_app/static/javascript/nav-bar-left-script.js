$(document).ready(function () {
    $(".page-status").hover(function () {
        $(this).parent().children("label").stop().fadeToggle()
    });
});