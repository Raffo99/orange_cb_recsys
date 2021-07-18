import { changeActiveBlock } from "./utils-functions.js";

$(document).ready(function () {
    if ($(".select-algorithm").val() == "GraphBasedRS") {
        $(".header-representations").css("display", "none");
        $(".div-content-representations").css("display", "none");
    }

    $("select").each(function () {
        changeActiveBlock($(this));
    });

    $("select").change(function () {
        if ($(this).val() == "ContentBasedRS") {
            $(".col-8").removeClass("col-8").addClass("col-6");
            $(".header-representations").slideToggle(function () {
                $(".div-content-representations").slideToggle();
            });
        } else if ($(this).val() == "GraphBasedRS") {
            $(".div-content-representations").slideToggle(function () {
                $(".header-representations").slideToggle(function () {
                      $(".col-6").removeClass("col-6").addClass("col-8");
                });
            });
        }
        changeActiveBlock($(this));
    });
});

