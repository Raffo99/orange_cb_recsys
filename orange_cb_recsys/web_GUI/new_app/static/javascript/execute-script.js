$(document).ready(function () {
    $(".add-item-button").click(function () {
        $(this).parent().parent().children(".list-possible-parameter").append(
            "<div class='item-possible-parameter'>"
            + "<input type='text'><img class='delete-item' src='../../static/icons/delete-icon.svg'>"
            + "</div>"
            )
    });

    $(".list-possible-parameter").on("click", ".delete-item", function () {
        $(this).parent().remove();
    });

    $(".fit-button-predict").click(function () {
        let itemsList = []
        $("#items-list").children(".item-possible-parameter").each(function () {
            itemsList.push($(this).children("input").val());
        });

        let usersList = []
        $("#users-list").children(".item-possible-parameter").each(function () {
            usersList.push($(this).children("input").val());
        })

        $.ajax({
            type: 'POST',
            url: "/execute-modules",
            contentType: 'application/json; charset=UTF-8',
            data: JSON.stringify({
                "module": "RecSys",
                "method": "multiple_fit_predict",
                "params": {
                    "user_id_list": usersList,
                    "filter_list": itemsList
                }
            }),
            success: function (data) {
                window.location.replace("/logger?module=RecSys")
            },
            error: function (jqXhr, textStatus, errorMessage) {
                console.log(errorMessage);
            }
        });
    });

    $(".fit-button").click(function () {
       let nameModule = $(this).parent().parent().children(".header-module").attr('name');

       if (nameModule == "ContentAnalyzer") {
           let logger = $("#logger");
           let contentType = $("input[name='content-type-analyzer']:checked").val();

           $.ajax({
               type: 'POST',
               url: "/execute-modules",
               contentType: 'application/json; charset=UTF-8',
               data: JSON.stringify({
                   "module": "ContentAnalyzer",
                   "contentType": contentType
               }),
               success: function (data) {
                    window.location.replace("/logger?module=ContentAnalyzer&contentType=" + contentType)
               },
               error: function (jqXhr, textStatus, errorMessage) {
                    console.log(errorMessage);
               }
           });
       }
    });

    $(".config-button").click(function () {
        let nameModule = $(this).parent().parent().children(".header-module").attr('name');
        console.log(nameModule)
        let contentType = $("input[name='content-type-analyzer']:checked").val();

        $.ajax({
            type: 'POST',
            url: "/save-config-file",
            contentType: 'application/json; charset=UTF-8',
            data: JSON.stringify({
                "module": nameModule,
                "contentType": contentType
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