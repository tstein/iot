"use strict";


var washerConfig = {
  type: 'line',
  data: {
      labels: [],
      datasets: [{
          label: 'washer red',
          backgroundColor: "#ff0000",
          borderColor: "#ff0000",
          data: []
      }]
  },
  options: {
      scales: {
          yAxes: [{
              ticks: {
                  beginAtZero:true
              }
          }],
          xAxes: [{
              type: "time",
          }]
      }
  }
}

var dryerConfig = {
  type: 'line',
  data: {
      labels: [],
      datasets: [{
          label: 'dryer shakeage',
          backgroundColor: "#0000ff",
          borderColor: "#0000ff",
          data: []
      }]
  },
  options: {
      scales: {
          yAxes: [{
              ticks: {
                  beginAtZero:true
              }
          }],
          xAxes: [{
              type: "time",
          }]
      }
  }
}

function updateGraph(chart, config, data) {
    var xs = data.map(function(d) { return d[0]; });
    var ys = data.map(function(d) { return d[1]; });
    config.data.datasets[0].data = xs;
    config.data.labels = ys;
    chart.update();
}

function pollWasher() {
    var callback = function() {
        var data = JSON.parse(this.responseText);
        (function(data) {
            updateGraph(window.washerChart, washerConfig, data);
        })(data);
        setTimeout(pollWasher, 1000);
    }
    var req = new XMLHttpRequest();
    req.addEventListener("load", callback);
    req.open("GET", "/washer_red");
    req.send();
}

function pollDryer() {
    var callback = function() {
        var data = JSON.parse(this.responseText);
        (function(data) {
            updateGraph(window.dryerChart, dryerConfig, data);
        })(data);
        setTimeout(pollDryer, 1000);
    }
    var req = new XMLHttpRequest();
    req.addEventListener("load", callback);
    req.open("GET", "/dryer_accel");
    req.send();
}

function setupGraphs() {
    var washerCtx = document.getElementById("washer-chart").getContext('2d');
    var dryerCtx = document.getElementById("dryer-chart").getContext('2d');
    window.washerChart = new Chart(washerCtx, washerConfig);
    window.dryerChart = new Chart(dryerCtx, dryerConfig);

    pollWasher();
    pollDryer();
}

window.onload = setupGraphs;
