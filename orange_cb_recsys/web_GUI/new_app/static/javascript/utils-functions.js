// Support method used to generate the JSON of the classes of the current active field representations
export function getClassWithParameters(blockParameter) {
    const types = {
        "text": "str",
        "number": "int",
        "checkbox": "bool"
    }

    if (blockParameter.children("[class='block-union-selection']").length > 0) {
        // Parameter is Union
        let parameters = [];
        blockParameter.children("[class='block-union-parameter']").children("[class*='block-parameter']").each(function () {
            parameters.push(getClassWithParameters($(this)));
        });

        blockParameter.children("[class='block-union-selection']").children("select").children("option").each(function (index) {
            parameters[index]["name"] = $(this).val();
        });

        return {
            'name': blockParameter.children("[class='block-union-selection']").children("label").text(),
            'type': 'Union',
            'value': blockParameter.children("[class='block-union-selection']").children("select").val(),
            'params': parameters
        }
    } else {
        let blockParameterContainer = (blockParameter.children("[class*='block-parameter-container']"));

        if (blockParameterContainer.children("[class*='block-sub-classes']").length > 0) {
            // Parameter is Complex with sub classes
            let subClasses = [];
            let blockSubClasses = blockParameterContainer.children("[class='block-sub-classes']");
            blockSubClasses.children("[class*='block-parameter']").each(function () {
                subClasses.push(getClassWithParameters($(this)));
            });

            blockParameterContainer.children("[class='block-sub-classes-selection']").children("select").children("option").each(function (index) {
               subClasses[index]["name"] = $(this).val();
            });

            return {
                'name': blockParameterContainer.children("[class='block-sub-classes-selection']").children("label").text(),
                'type': 'Complex',
                'value': blockParameterContainer.children("[class='block-sub-classes-selection']").children("select").val(),
                'sub_classes': subClasses
            }
        } else if (blockParameterContainer.children("[class='block-parameter']").length > 0
                        || blockParameterContainer.length == 0) {
            // Parameter is Complex with parameters
            let parameters = [];
            blockParameterContainer.children("[class*='block-parameter']").each(function () {
                parameters.push(getClassWithParameters($(this)));
            });

            return {
                'name': blockParameterContainer.children("label").text(),
                'type': 'Complex',
                'params': parameters
            }
        } else if (blockParameterContainer.children("[class='wrapper-kwargs']").length > 0) {
            let divListArgs = blockParameterContainer.children(".wrapper-kwargs").children(".list-kwargs");
            let argsDict = {}
            divListArgs.children(".item-kwargs").each(function () {
                argsDict[$(this).children(".nameArg").val()] = $(this).children(".valueArg").val();
            });

            return {
                "name": "kwargs",
                "type": "kwargs",
                "params": argsDict
            }
        } else if (blockParameterContainer.children("[class='exo-list']").length > 0) {
            console.log("test");
            let nameParameter = blockParameterContainer.children("label").text()
            let listType = "Items";
            if (nameParameter.includes("Users")) listType = "Users";
            let listUse = [];

            blockParameterContainer.children(".exo-list").children(".exo-prop").each(function () {
                if ($(this).children("input").is(":checked")) listUse.push($(this).children("label").text());
            });

            console.log(listUse)
            return {
                "name": nameParameter,
                "type": "exogenous_props",
                "listType": listType,
                "list": listUse
            }
        } else {
            let value = blockParameterContainer.children("input").attr("type") == "checkbox" ?
                blockParameterContainer.children("input").is(":checked") :
                blockParameterContainer.children("input").val();
            // Parameter is Simple
            return {
                'name': blockParameterContainer.children("label").text(),
                'type': types[blockParameterContainer.children("input").attr('type')],
                'value': value
            }
        }
    }
}

export function changeActiveBlock(selectObj) {
    let nameToActive = selectObj.find('option:selected').attr('value').replace(" ", "");
    let nameParam = selectObj.attr('name');
    let nameClassBlockParameter = "." + selectObj.parent().parent().children().eq(1).attr('class');
    let blockUnionParameterRelative = selectObj.parent().parent().find(nameClassBlockParameter);
    let toRemove = blockUnionParameterRelative.find(".active-block");
    let toAdd = blockUnionParameterRelative.find("[name='" + nameParam + "-" + nameToActive + "']");

    toRemove.css("display", "");
    toRemove.removeClass("active-block");
    toAdd.addClass("active-block");

    if (!toAdd.hasClass("empty")) {
        toAdd.fadeIn();
        toAdd.css("display", "block");
        toAdd.find("select").each(function () {
            changeActiveBlock($(this));
        });
    }

}

export function fixName(name, isAlgorithmName) {
    return (isAlgorithmName ? name.trim().replace("\n", "").replace(" ", "_") :
        name.trim().replace("\n", "").replace(" ", "_").toLowerCase());
}

export function showToast(message, timeDisplay) {
    $("#toast").children("label").text(message);
    $("#toast").fadeIn();

    setTimeout(function () {
        $("#toast").fadeOut();
    }, timeDisplay);
}