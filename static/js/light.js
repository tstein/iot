"use strict";

var poll_interval = 500;

function updateState(state) {
    document.getElementById("light-status").innerHTML = "it's " + state;
    if (state == "on") {
        document.getElementById("body").classList.add("body-light-on");
        document.getElementById("body").classList.remove("body-light-off");
    } else {
        document.getElementById("body").classList.add("body-light-off");
        document.getElementById("body").classList.remove("body-light-on");
    }
}

function pollState() {
    var xmlHttp = new XMLHttpRequest();
    xmlHttp.onreadystatechange = function() {
        if (xmlHttp.readyState == 4) {
            if (xmlHttp.status == 200) {
                updateState(xmlHttp.responseText);
            }

            setTimeout(pollState, poll_interval);
        }
    }
    xmlHttp.open("GET", "/state", true);
    xmlHttp.send(null);
}

(function() {
    pollState();
})();
