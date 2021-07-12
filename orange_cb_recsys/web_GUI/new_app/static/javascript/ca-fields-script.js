window.onload = function() {
    let listChecked = document.querySelectorAll('[type*="checkbox"]');
    let listRadio = document.querySelectorAll('[type*="radio"]');

    listChecked.forEach(el => {
        let checked = JSON.parse(sessionStorage.getItem(el.id));
        document.getElementById(el.id).checked = checked;
    });

    listRadio.forEach(el => {
        let checked = JSON.parse(sessionStorage.getItem(el.id));
        document.getElementById(el.id).checked = checked;
    });
}

window.onunload = function()  {
    let listChecked = document.querySelectorAll('[type*="checkbox"]');
    let listRadio =  document.querySelectorAll('[type*="radio"]');

    listChecked.forEach( el => {
        sessionStorage.setItem(el.id, el.checked);
    });

    listRadio.forEach( el => {
        sessionStorage.setItem(el.id, el.checked);
    });
}
