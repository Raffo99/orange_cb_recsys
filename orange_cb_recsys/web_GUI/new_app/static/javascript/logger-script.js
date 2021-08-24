let $_GET = {};

if(document.location.toString().indexOf('?') !== -1) {
    var query = document.location
                   .toString()
                   // get the query string
                   .replace(/^.*?\?/, '')
                   // and remove any existing hash string (thanks, @vrijdenker)
                   .replace(/#.*$/, '')
                   .split('&');

    for(var i=0, l=query.length; i<l; i++) {
       var aux = decodeURIComponent(query[i]).split('=');
       $_GET[aux[0]] = aux[1];
    }
}

function updateLogger() {
    let logger = $("#logger");

    $.ajax({
        type: 'POST',
        url: "/get-logger",
        contentType: 'application/json; charset=UTF-8',
        data: JSON.stringify({
            "module": $_GET["module"],
            "content_type": $_GET["contentType"]
        }),
        success: function (data) {
             let toAppend = JSON.parse(data)["log"];
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
