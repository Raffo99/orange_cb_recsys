import { showToast } from "./utils-functions.js";

$(document).ready(function () {
    $(".page-status").hover(function () {
        $(this).parent().children("label").stop().fadeToggle();
    });

    $("#save-button").hover(function () {
        $(this).children("label").stop().fadeToggle();
    })

    $("#content-analyzer").children(".pages").children(".page").children(".page-status").click(function () {
        let toActiveName = $(this).parent().children("label").text().toLowerCase();
        let toRemoveName = "";

        if ($("#content-analyzer").children(".sub-pages.active-sub-pages").length > 0) {
            toRemoveName = $("#content-analyzer").children(".sub-pages.active-sub-pages").attr('name').replace("sub-pages-", "").toLowerCase();

            $("#content-analyzer").children(".sub-pages.active-sub-pages").animate({width: 'toggle'}, function () {
                $(this).removeClass("active-sub-pages");
            });
        }

        if (toRemoveName != toActiveName) {
            $("#content-analyzer").children("[name='sub-pages-" + toActiveName + "']").animate({width: 'toggle'}, function () {
                $("#content-analyzer").children("[name='sub-pages-" + toActiveName + "']").addClass("active-sub-pages");
            });

            $("#content-analyzer").children("[name='sub-pages-" + toActiveName + "']").css("display", "flex");
        }
    });


    $("#save-button").click(function () {
        $.ajax({
            url: "/save-current-project",
            type: "post",
            dataType: "json",
            contentType: "application/json",
            data: JSON.stringify({"delete_old": false}),
            success: function(data) {
                if (data["result"] == "Question") {
                    let dialogOverlay = $("#overlay").children("#dialog");

                    dialogOverlay.children("#dialog-question").text("There is already a file in that directory, do you want to replace it?");

                    dialogOverlay.children("#dialog-buttons").children("#dialog-yes").click(function () {
                        $("#overlay").fadeOut();

                        $.ajax({
                            url: "/save-current-project",
                            type: "post",
                            dataType: "json",
                            contentType: "application/json",
                            data: JSON.stringify({"delete_old": true}),
                            success: function (data) {
                                let message = "";

                                if (data["result"] == "True")
                                    message = "Project saved successfully!";
                                else
                                    message = "There was a error in the saving!";

                                showToast(message, 2000);
                            }
                        });
                    });

                    dialogOverlay.children("#dialog-buttons").children("#dialog-no").click(function () {
                        $("#overlay").fadeOut();
                    });

                    $("#overlay").fadeIn();
                    $("#overlay").css("display", "flex");
                } else {
                    let message = "";

                    if (data["result"] == "True")
                        message = "Project saved successfully!";
                    else
                        message = "There was a error in the saving!";

                    showToast(message, 2000);
                }
            },
            error: function() {
                alert("Error");
            }
        })
    });
});