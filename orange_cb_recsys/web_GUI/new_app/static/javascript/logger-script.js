function updateLogger() {
    let logger = $("#logger");

    $.ajax({
        type: 'POST',
        url: "/get-logger",
        contentType: 'application/json; charset=UTF-8',
        success: function (data) {
             let toAppend = JSON.parse(data)["log"];
             console.log(toAppend);
             if (toAppend != "CLOSED") {
                logger.empty();
                logger.append(toAppend);
             }
        }
    });
}

setInterval(function () {
    updateLogger()
}, 5000);


$(document).ready(function () {
    updateLogger();
});
