$(document).ready(function () {
    $(".fit-button").click(function () {
       let nameModule = $(this).parent().parent().children(".header-module").attr('name');

       if (nameModule == "ContentAnalyzer") {
           let logger = $("#logger");
           console.log("send");
           $.ajax({
               type: 'POST',
               url: "/execute-modules",
               contentType: 'application/json; charset=UTF-8',
               data: JSON.stringify({
                   "module": "ContentAnalyzer"
               }),
               success: function (data) {
                    let toAppend = JSON.parse(data)["result"];
                    logger.append(toAppend);
               },
               error: function (jqXhr, textStatus, errorMessage) {
                    console.log(errorMessage);
               }
           });
       }
    });

    $(".config-button").click(function () {
        let nameModule = $(this).parent().parent().children(".header-module").attr('name');

        $.ajax({
            type: 'POST',
            url: "/save-config-file",
            contentType: 'application/json; charset=UTF-8',
            data: JSON.stringify({
                "module": nameModule
            }),
            success: function(data) {
                console.log(data)
            },
            error: function (jqXhr, textStatus, errorMessage) {
                console.log(errorMessage);
            }
        });
    });
});