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
    toAdd.fadeIn();
    toAdd.css("display", "block");

    toAdd.find("select").each(function () {
        changeActiveBlock($(this));
    });
}

export function fixName(name, isAlgorithmName) {
    return (isAlgorithmName ? name.trim().replace("\n", "").replace(" ", "_") :
        name.trim().replace("\n", "").replace(" ", "_").toLowerCase());
}