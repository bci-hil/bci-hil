'use strict';

const socket_to_use = "ws://localhost:6581/";
let server_is_up_and_running = false;
let ws;

let stimuli_sequence = [];
let session_start_timestamp = Date.now();
let session_is_running = false;

const chart_holder = document.getElementById("chart_holder");
let chart_ctx = document.getElementById("chart-area").getContext("2d");
const chart2_holder = document.getElementById("chart2_holder");
let chart2_ctx = document.getElementById("chart2-area").getContext("2d");
const chart3_holder = document.getElementById("chart3_holder");
let chart3_ctx = document.getElementById("chart3-area").getContext("2d");
const chart4_holder = document.getElementById("chart4_holder");
let chart4_ctx = document.getElementById("chart4-area").getContext("2d");

function start_session() {
  console.log("Start calibration clicked!");
  let user_no = parseInt(document.getElementById("user_no").value)
  if (server_is_up_and_running == true) {
    try {
      ws.send(JSON.stringify({ action: "start", timestamp: Date.now(), user_no: user_no}));
    } catch {}
  }
  session_start_timestamp = Date.now();
  document.getElementById('cancel').disabled = false;
  document.getElementById('stop').disabled = false;
  document.getElementById('start').disabled = true;

  stimuli_sequence = [];
  init_stimuli_histogram()
  document.getElementById('stimuli_sequence').innerHTML = '';
  session_is_running = true;
}

function increase_user_no() {
  let user_no = parseInt(document.getElementById("user_no").value);
  document.getElementById("user_no").value = ("000" + (user_no + 1)).substr(-4,4);
}

function stop_session() {
  console.log("Stop calibration clicked!");
  if (server_is_up_and_running == true) {
    try {
      ws.send(JSON.stringify({ action: "stop", timestamp: Date.now()}));
    } catch {}
  }
  document.getElementById('stop').disabled = true;
  document.getElementById('start').disabled = false;
  session_is_running = false;

  const myTimeout = setTimeout(increase_user_no, 1000);
}

function cancel_session () {
  console.log("Cancel calibration clicked!");
  if (server_is_up_and_running == true) {
    try {
      ws.send(JSON.stringify({ action: "cancel", timestamp: Date.now()}));
    } catch {}
  }
  document.getElementById('cancel').disabled = false;
  document.getElementById('start').disabled = false;
  document.getElementById('stop').disabled = true;
  session_is_running = false;

  const myTimeout = setTimeout(increase_user_no, 1000);
}

// Consider removing the accumulation option and start data accumulation directly upon session start.
function start_accumulation() {
  console.log("Start accumulation clicked!");

  if (server_is_up_and_running == true) {
    try {
      ws.send(JSON.stringify({ action: "accumulate", timestamp: Date.now()}));
    } catch {}
  }
}

function start_fitting() {
  console.log("Start fitting clicked!");

  if (server_is_up_and_running == true) {
    try {
      ws.send(JSON.stringify({ action: "start_fitting", timestamp: Date.now()}));
    } catch {}
  }
}

function set_user_no() {
  console.log("Set user number clicked!");
  let user_no = parseInt(document.getElementById("user_no").value)
  if (server_is_up_and_running == true) {
    try {
      ws.send(JSON.stringify({ action: "set_user_no", timestamp: Date.now(), user_no: user_no}));
    } catch {}
  }
}


function goFullscreen() {
  // element which needs to enter full-screen mode
  var element = document.querySelector("#contento");
  // make the element go to full-screen mode
  element.requestFullscreen()
    .then(function() {
      // element has entered fullscreen mode successfully
    })
    .catch(function(error) {
      // element could not enter fullscreen mode
    });
}


// MIT License:
//
// Copyright (c) 2010-2012, Joe Walnes
//
// Permission is hereby granted, free of charge, to any person obtaining a copy
// of this software and associated documentation files (the "Software"), to deal
// in the Software without restriction, including without limitation the rights
// to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
// copies of the Software, and to permit persons to whom the Software is
// furnished to do so, subject to the following conditions:
//
// The above copyright notice and this permission notice shall be included in
// all copies or substantial portions of the Software.
//
// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
// IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
// FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
// AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
// LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
// OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
// THE SOFTWARE.

/**
 * This behaves like a WebSocket in every way, except if it fails to connect,
 * or it gets disconnected, it will repeatedly poll until it successfully connects
 * again.
 *
 * It is API compatible, so when you have:
 *   ws = new WebSocket('ws://....');
 * you can replace with:
 *   ws = new ReconnectingWebSocket('ws://....');
 *
 * The event stream will typically look like:
 *  onconnecting
 *  onopen
 *  onmessage
 *  onmessage
 *  onclose // lost connection
 *  onconnecting
 *  onopen  // sometime later...
 *  onmessage
 *  onmessage
 *  etc...
 *
 * It is API compatible with the standard WebSocket API, apart from the following members:
 *
 * - `bufferedAmount`
 * - `extensions`
 * - `binaryType`
 *
 * Latest version: https://github.com/joewalnes/reconnecting-websocket/
 * - Joe Walnes
 *
 * Syntax
 * ======
 * var socket = new ReconnectingWebSocket(url, protocols, options);
 *
 * Parameters
 * ==========
 * url - The url you are connecting to.
 * protocols - Optional string or array of protocols.
 * options - See below
 *
 * Options
 * =======
 * Options can either be passed upon instantiation or set after instantiation:
 *
 * var socket = new ReconnectingWebSocket(url, null, { debug: true, reconnectInterval: 4000 });
 *
 * or
 *
 * var socket = new ReconnectingWebSocket(url);
 * socket.debug = true;
 * socket.reconnectInterval = 4000;
 *
 * debug
 * - Whether this instance should log debug messages. Accepts true or false. Default: false.
 *
 * automaticOpen
 * - Whether or not the websocket should attempt to connect immediately upon instantiation. The socket can be manually opened or closed at any time using ws.open() and ws.close().
 *
 * reconnectInterval
 * - The number of milliseconds to delay before attempting to reconnect. Accepts integer. Default: 1000.
 *
 * maxReconnectInterval
 * - The maximum number of milliseconds to delay a reconnection attempt. Accepts integer. Default: 30000.
 *
 * reconnectDecay
 * - The rate of increase of the reconnect delay. Allows reconnect attempts to back off when problems persist. Accepts integer or float. Default: 1.5.
 *
 * timeoutInterval
 * - The maximum time in milliseconds to wait for a connection to succeed before closing and retrying. Accepts integer. Default: 2000.
 *
 */
(function (global, factory) {
    if (typeof define === 'function' && define.amd) {
        define([], factory);
    } else if (typeof module !== 'undefined' && module.exports){
        module.exports = factory();
    } else {
        global.ReconnectingWebSocket = factory();
    }
})(this, function () {

    if (!('WebSocket' in window)) {
        return;
    }

    function ReconnectingWebSocket(url, protocols, options) {

        // Default settings
        var settings = {

            /** Whether this instance should log debug messages. */
            debug: false,

            /** Whether or not the websocket should attempt to connect immediately upon instantiation. */
            automaticOpen: true,

            /** The number of milliseconds to delay before attempting to reconnect. */
            reconnectInterval: 500,
            /** The maximum number of milliseconds to delay a reconnection attempt. */
            maxReconnectInterval: 3000,
            /** The rate of increase of the reconnect delay. Allows reconnect attempts to back off when problems persist. */
            reconnectDecay: 1.5,

            /** The maximum time in milliseconds to wait for a connection to succeed before closing and retrying. */
            timeoutInterval: 2000,

            /** The maximum number of reconnection attempts to make. Unlimited if null. */
            maxReconnectAttempts: null,

            /** The binary type, possible values 'blob' or 'arraybuffer', default 'blob'. */
            binaryType: 'blob'
        }
        if (!options) { options = {}; }

        // Overwrite and define settings with options if they exist.
        for (var key in settings) {
            if (typeof options[key] !== 'undefined') {
                this[key] = options[key];
            } else {
                this[key] = settings[key];
            }
        }

        // These should be treated as read-only properties

        /** The URL as resolved by the constructor. This is always an absolute URL. Read only. */
        this.url = url;

        /** The number of attempted reconnects since starting, or the last successful connection. Read only. */
        this.reconnectAttempts = 0;

        /**
         * The current state of the connection.
         * Can be one of: WebSocket.CONNECTING, WebSocket.OPEN, WebSocket.CLOSING, WebSocket.CLOSED
         * Read only.
         */
        this.readyState = WebSocket.CONNECTING;

        /**
         * A string indicating the name of the sub-protocol the server selected; this will be one of
         * the strings specified in the protocols parameter when creating the WebSocket object.
         * Read only.
         */
        this.protocol = null;

        // Private state variables

        var self = this;
        var ws;
        var forcedClose = false;
        var timedOut = false;
        var eventTarget = document.createElement('div');

        // Wire up "on*" properties as event handlers

        eventTarget.addEventListener('open',       function(event) { self.onopen(event); });
        eventTarget.addEventListener('close',      function(event) { self.onclose(event); });
        eventTarget.addEventListener('connecting', function(event) { self.onconnecting(event); });
        eventTarget.addEventListener('message',    function(event) { self.onmessage(event); });
        eventTarget.addEventListener('error',      function(event) { self.onerror(event); });

        // Expose the API required by EventTarget

        this.addEventListener = eventTarget.addEventListener.bind(eventTarget);
        this.removeEventListener = eventTarget.removeEventListener.bind(eventTarget);
        this.dispatchEvent = eventTarget.dispatchEvent.bind(eventTarget);

        /**
         * This function generates an event that is compatible with standard
         * compliant browsers and IE9 - IE11
         *
         * This will prevent the error:
         * Object doesn't support this action
         *
         * http://stackoverflow.com/questions/19345392/why-arent-my-parameters-getting-passed-through-to-a-dispatched-event/19345563#19345563
         * @param s String The name that the event should use
         * @param args Object an optional object that the event will use
         */
        function generateEvent(s, args) {
          var evt = document.createEvent("CustomEvent");
          evt.initCustomEvent(s, false, false, args);
          return evt;
        };

        this.open = function (reconnectAttempt) {
            ws = new WebSocket(self.url, protocols || []);
            ws.binaryType = this.binaryType;

            if (reconnectAttempt) {
                if (this.maxReconnectAttempts && this.reconnectAttempts > this.maxReconnectAttempts) {
                    return;
                }
            } else {
                eventTarget.dispatchEvent(generateEvent('connecting'));
                this.reconnectAttempts = 0;
            }

            if (self.debug || ReconnectingWebSocket.debugAll) {
                console.debug('ReconnectingWebSocket', 'attempt-connect', self.url);
            }

            var localWs = ws;
            var timeout = setTimeout(function() {
                if (self.debug || ReconnectingWebSocket.debugAll) {
                    console.debug('ReconnectingWebSocket', 'connection-timeout', self.url);
                }
                timedOut = true;
                localWs.close();
                timedOut = false;
            }, self.timeoutInterval);

            ws.onopen = function(event) {
                clearTimeout(timeout);
                if (self.debug || ReconnectingWebSocket.debugAll) {
                    console.debug('ReconnectingWebSocket', 'onopen', self.url);
                }
                self.protocol = ws.protocol;
                self.readyState = WebSocket.OPEN;
                self.reconnectAttempts = 0;
                var e = generateEvent('open');
                e.isReconnect = reconnectAttempt;
                reconnectAttempt = false;
                eventTarget.dispatchEvent(e);
            };

            ws.onclose = function(event) {
                clearTimeout(timeout);
                ws = null;
                if (forcedClose) {
                    self.readyState = WebSocket.CLOSED;
                    eventTarget.dispatchEvent(generateEvent('close'));
                } else {
                    self.readyState = WebSocket.CONNECTING;
                    var e = generateEvent('connecting');
                    e.code = event.code;
                    e.reason = event.reason;
                    e.wasClean = event.wasClean;
                    eventTarget.dispatchEvent(e);
                    if (!reconnectAttempt && !timedOut) {
                        if (self.debug || ReconnectingWebSocket.debugAll) {
                            console.debug('ReconnectingWebSocket', 'onclose', self.url);
                        }
                        eventTarget.dispatchEvent(generateEvent('close'));
                    }

                    var timeout = self.reconnectInterval * Math.pow(self.reconnectDecay, self.reconnectAttempts);
                    setTimeout(function() {
                        self.reconnectAttempts++;
                        self.open(true);
                    }, timeout > self.maxReconnectInterval ? self.maxReconnectInterval : timeout);
                }
            };
            ws.onmessage = function(event) {
                if (self.debug || ReconnectingWebSocket.debugAll) {
                    console.debug('ReconnectingWebSocket', 'onmessage', self.url, event.data);
                }
                var e = generateEvent('message');
                e.data = event.data;
                eventTarget.dispatchEvent(e);
            };
            ws.onerror = function(event) {
                if (self.debug || ReconnectingWebSocket.debugAll) {
                    console.debug('ReconnectingWebSocket', 'onerror', self.url, event);
                }
                eventTarget.dispatchEvent(generateEvent('error'));
            };
        }

        // Whether or not to create a websocket upon instantiation
        if (this.automaticOpen == true) {
            this.open(false);
        }

        /**
         * Transmits data to the server over the WebSocket connection.
         *
         * @param data a text string, ArrayBuffer or Blob to send to the server.
         */
        this.send = function(data) {
            if (ws) {
                if (self.debug || ReconnectingWebSocket.debugAll) {
                    console.debug('ReconnectingWebSocket', 'send', self.url, data);
                }
                return ws.send(data);
            } else {
                throw 'INVALID_STATE_ERR : Pausing to reconnect websocket';
            }
        };

        /**
         * Closes the WebSocket connection or connection attempt, if any.
         * If the connection is already CLOSED, this method does nothing.
         */
        this.close = function(code, reason) {
            // Default CLOSE_NORMAL code
            if (typeof code == 'undefined') {
                code = 1000;
            }
            forcedClose = true;
            if (ws) {
                ws.close(code, reason);
            }
        };

        /**
         * Additional public API method to refresh the connection if still open (close, re-open).
         * For example, if the app suspects bad data / missed heart beats, it can try to refresh.
         */
        this.refresh = function() {
            if (ws) {
                ws.close();
            }
        };
    }

    /**
     * An event listener to be called when the WebSocket connection's readyState changes to OPEN;
     * this indicates that the connection is ready to send and receive data.
     */
    ReconnectingWebSocket.prototype.onopen = function(event) {};
    /** An event listener to be called when the WebSocket connection's readyState changes to CLOSED. */
    ReconnectingWebSocket.prototype.onclose = function(event) {};
    /** An event listener to be called when a connection begins being attempted. */
    ReconnectingWebSocket.prototype.onconnecting = function(event) {};
    /** An event listener to be called when a message is received from the server. */
    ReconnectingWebSocket.prototype.onmessage = function(event) {};
    /** An event listener to be called when an error occurs. */
    ReconnectingWebSocket.prototype.onerror = function(event) {};

    /**
     * Whether all instances of ReconnectingWebSocket should log debug messages.
     * Setting this to true is the equivalent of setting all instances of ReconnectingWebSocket.debug to true.
     */
    ReconnectingWebSocket.debugAll = false;

    ReconnectingWebSocket.CONNECTING = WebSocket.CONNECTING;
    ReconnectingWebSocket.OPEN = WebSocket.OPEN;
    ReconnectingWebSocket.CLOSING = WebSocket.CLOSING;
    ReconnectingWebSocket.CLOSED = WebSocket.CLOSED;

    return ReconnectingWebSocket;
});


function set_server_status (is_up) {
  if ((is_up == true) && (server_is_up_and_running == false)) {
    document.getElementById("header").style.background = "none";
    document.getElementById("header").style.color = "#ffffff";
    document.getElementById("header").style.opacity = 0.8;
    document.querySelector(".users").textContent = "";
  } else if ((is_up == false) && (server_is_up_and_running == true)) {
    document.getElementById("header").style.background = "#800000";
    document.getElementById("header").style.color = "#9e4a4a";
    document.getElementById("header").style.opacity = 1.0;
    document.querySelector(".users").textContent = "The engine isn't up and running";
  }
  server_is_up_and_running = is_up;
}


let last_timestamp = -1;
let last_elapsed_seconds = -1;
let recording_opacity = 0.0;

function animate (timestamp) {
  let milliseconds_since_last_animate = timestamp - last_timestamp;
  last_timestamp = timestamp;
  // 60 Hz screen:  8079.115  8095.795      diff = 16,68
  // 120Hz screen:  3345.732  3354.065      diff =  8,333

  let animate_now = Date.now();
  document.getElementById("timestamp").innerHTML = animate_now;

  if (session_is_running == true) {
    let elapsed_seconds = Math.floor((animate_now - session_start_timestamp) / 1000);
    if (last_elapsed_seconds != elapsed_seconds) {
      document.getElementById("elapsed_seconds").innerHTML = elapsed_seconds;
      last_elapsed_seconds = elapsed_seconds;
    }
  }

  recording_opacity = recording_opacity - milliseconds_since_last_animate / 1000.0;
  recording_opacity = Math.max(0.0,recording_opacity);
  document.getElementById("recording").style.opacity = recording_opacity;

  window.requestAnimationFrame(animate);
}

function clicked_plus () {
  ws.send(JSON.stringify({ action: "plus" }));
}

function clicked_minus () {
  ws.send(JSON.stringify({ action: "minus" }));
}


// This is the true probability distribution:
function std_normal_distribution (x, A, sigma2) {
  // Return the probability density function, pdf:
  // A = mean
  // sigma2 = variance = std_deviation^2
  return Math.exp(-Math.pow((x - A),2) / (2*sigma2)) / (Math.sqrt(2 * sigma2 * Math.PI));
}

// Monte Carlo simulation stuff below
let nof_histogram_bins = 21;
let bin_min = -2.1;
let bin_max = 2.1;
let bin_width = (bin_max - bin_min) / nof_histogram_bins;
let histogram_labels = [];
let histogram_data = [];
let mc_ideal = [];
let histogram_dict = {};
let monte_carlo_data = [];

const yellow  = "rgba(195,191,0,0.80)";
const blue    = "rgba(63,56,255,0.80)";
const green   = "rgba(12,142,0,0.80)";
const red     = "rgba(198,0,0,0.80)";
const grey    = "rgba(140,140,140,0.80)";

/*
// The crown
let eeg_quality_dict = {"CP3":1,"C3":2,"F5":3,"PO3":4,"PO4":5,"F6":6,"C4":7,"CP4":8};

let eeg_quality_config = {
  type: 'bar',
  data: {
    labels: ["CP3","C3","F5","PO3", "PO4","F6","C4","CP4"],
    datasets: [{
        label: ["CP3","C3","F5","PO3", "PO4","F6","C4","CP4"],
        type: "bar",
        backgroundColor: ["rgba(200,100,200,0.80)",
        "rgba(200,120,200,0.80)",
        "rgba(200,140,200,0.80)",
        "rgba(200,160,200,0.80)",
        "rgba(200,180,200,0.80)",
        "rgba(200,200,200,0.80)",
        "rgba(200,220,200,0.80)",
        "rgba(200,240,200,0.80)"],
        borderColor: "rgba(0,0,0,0.80)",
        borderWidth: 1,
        data: []
      }
    ]
  },
  options: {
    plugins: {
      legend: {
        display: false
      }
    },
    scales: {
      y: {
        beginAtZero: true,
        display: true,
        grid: { color: "rgba(255,255,255,0.25)"},
        title: {
          display: true,
          text: '',
        }
      },
      x: { grid: { color: "rgba(255,255,255,0.0)"}, ticks:{font:{size:16}} },
    }
  }
};
*/

// museS
let eeg_quality_dict = {"TP9":1,"AF7":2,"AF8":3,"TP10":4};

let eeg_quality_config = {
  type: 'bar',
  data: {
    labels: ["TP9","AF7","AF8","TP10"],
    datasets: [{
        label: ["TP9","AF7","AF8","TP10"],
        type: "bar",
        backgroundColor: ["rgba(200,100,200,0.80)",
        "rgba(200,120,200,0.80)",
        "rgba(200,140,200,0.80)",
        "rgba(200,160,200,0.80)"],
        borderColor: "rgba(0,0,0,0.80)",
        borderWidth: 1,
        data: []
      }
    ]
  },
  options: {
    plugins: {
      legend: {
        display: false
      }
    },
    scales: {
      y: {
        beginAtZero: true,
        display: true,
        grid: { color: "rgba(255,255,255,0.25)"},
        title: {
          display: true,
          text: '',
        }
      },
      x: { grid: { color: "rgba(255,255,255,0.0)"}, ticks:{font:{size:16}} },
    }
  }
};

//let prediction_dict = {'hat':0.0,'tie':0.0,'briefcase':0.0,'skirt':0.0,'yellow':1.0,'blue':0.0,'green':0.0,'red':0.0,'child':0.0};
let prediction_dict = {'yellow':1.0,'blue':0.0,'green':0.0,'red':0.0,'child':0.0};

let prediction_config = {
  type: 'bar',
  data: {
    labels: histogram_labels,
    datasets: [{
        label: "Prediction",
        type: "bar",
        backgroundColor: [yellow,
        blue,
        green,
        red,
        grey],
        borderColor: "rgba(0,0,0,0.80)",
        borderWidth: 1,
        data: histogram_data
      }
    ]
  },
  options: {
    plugins: {
      legend: {
        display: false
      }
    },
    scales: {
      y: {
        beginAtZero: true,
        display: true,
        grid: { color: "rgba(255,255,255,0.25)"},
        title: {
          display: true,
          text: '',
        }
      },
      x: { grid: { color: "rgba(255,255,255,0.0)"}, ticks:{font:{size:16}} },
    }
  }
};


let histogram_config = {
  type: 'bar',
  data: {
    labels: histogram_labels,
    datasets: [{
        label: "Stimuli category histogram",
        type: "bar",
        backgroundColor: [yellow,
        blue,
        green,
        red,
        grey],
        borderColor: "rgba(0,0,0,0.80)",
        borderWidth: 1,
        data: histogram_data
      }
    ]
  },
  options: {
    plugins: {
      legend: {
        display: false
      }
    },
    scales: {
      y: {
        beginAtZero: true,
        display: true,
        grid: { color: "rgba(255,255,255,0.25)"},
        title: {
          display: true,
          text: 'No. times shown',
        }
      },
      x: { grid: { color: "rgba(255,255,255,0.0)"}, ticks:{font:{size:16}} },
    }
  }
};

let pie_config = {
  type: 'pie',
  data: {
    labels: histogram_labels,
    datasets: [{
        label: "Stimuli category pie chart",
        type: "pie",
        backgroundColor: [yellow,
        blue,
        green,
        red,
        grey],
        borderColor: "rgba(0,0,0,0.80)",
        borderWidth: 1,
        data: histogram_data
      }
    ]
  },
  options: {
    rotation: 90
  }
};

const nof_categories = 4;

// This is a dict of all categories and the stimuli_no that belongs to this category:
const stimuli_categories = {}
stimuli_categories['left'] = [0]
stimuli_categories['right'] = [1]
stimuli_categories['tounge'] = [2]
stimuli_categories['feet'] = [3]

const category_nos = {}
category_nos['left'] = 0
category_nos['right'] = 1
category_nos['tounge'] = 2
category_nos['feet'] = 3
category_nos['cancel'] = 999

const category_ids = {}
category_ids[0] = 'left'
category_ids[1] = 'right'
category_ids[2] = 'tounge'
category_ids[3] = 'feet'


function init_stimuli_histogram() {
  Chart.defaults.animation.duration = 700;
  Chart.defaults.font.size = 24;
  Chart.defaults.color = "white";
  chart_holder.style.height = "auto";
  chart_holder.style.width = "600px";
  histogram_dict = {};
  for (let category_no = 0; category_no < nof_categories; category_no++) {
    histogram_dict[category_no] = 0;
  }
  if (window.my_chart == null) {
    for (let category_no = 0; category_no < nof_categories; category_no++) {
      histogram_labels.push(category_ids[category_no]);
      histogram_data.push(0.0);
    }
    window.my_chart = new Chart(chart_ctx, histogram_config);
  }

  chart2_holder.style.height = "auto";
  chart2_holder.style.width = "500px";
  if (window.my_chart2 == null) {
    window.my_chart2 = new Chart(chart2_ctx, pie_config);
  }
}

function init_prediction_chart () {
  chart4_holder.style.height = "auto";
  chart4_holder.style.width = "500px";
  if (window.my_chart4 == null) {
    window.my_chart4 = new Chart(chart4_ctx, prediction_config);
  }
}

function update_prediction_chart(data) {
  //console.log("updating prediction chart with data:");
  //console.log(data);
  //data={"CP3":1430.321234,"C3":2430.321234,"F5":7430.321234,"PO3":7430.321234,"PO4":7430.321234,"F6":7430.321234,"C4":7430.321234,"CP4":7430.321234}
  //let prediction_dict = {'hat':0.0,'tie':0.0,'briefcase':0.0,'skirt':0.0,'yellow':1.0,'blue':0.0,'green':0.0,'red':0.0,'child':0.0};
  //let prediction_dict = {'yellow':1.0,'blue':0.0,'green':0.0,'red':0.0,'child':0.0};
  // Removing obsolete categories:
  delete data['hat'];
  delete data['tie'];
  delete data['briefcase'];
  delete data['skirt'];
  data['child'] = 0.0;
  prediction_dict = data;
  window.my_chart4.data.datasets[0].data = Object.keys(prediction_dict).map(function (key) { return prediction_dict[key]; });
  //console.log(window.my_chart4.data.datasets[0].data);
  window.my_chart4.update();
}


function init_eeg_quality_chart () {
  chart3_holder.style.height = "auto";
  chart3_holder.style.width = "500px";
  if (window.my_chart3 == null) {
    window.my_chart3 = new Chart(chart3_ctx, eeg_quality_config);
  }
}

function update_eeg_quality_chart(data) {
  //console.log("updating with data:");
  //console.log(data);
  //data={"CP3":1430.321234,"C3":2430.321234,"F5":7430.321234,"PO3":7430.321234,"PO4":7430.321234,"F6":7430.321234,"C4":7430.321234,"CP4":7430.321234}
  eeg_quality_dict = data;
  window.my_chart3.data.datasets[0].data = Object.keys(eeg_quality_dict).map(function (key) { return eeg_quality_dict[key]; });
  //console.log(window.my_chart3.data.datasets[0].data);
  window.my_chart3.update();
}


function update_stimuli_histogram(next_stimuli) {
  for (let this_category_id in stimuli_categories) {
    for (let perhaps_stimuli_no in stimuli_categories[this_category_id]) {
      if (next_stimuli == stimuli_categories[this_category_id][perhaps_stimuli_no]) {
        let category_no = category_nos[this_category_id];
        histogram_dict[category_no] += 1;
      }
    }
  }
  window.my_chart.data.datasets[0].data = Object.keys(histogram_dict).map(function (key) { return histogram_dict[key]; });
//  window.my_chart.data.datasets[0].label = "Epoch number #";
  window.my_chart.update();

  window.my_chart2.data.datasets[0].data = Object.keys(histogram_dict).map(function (key) { return histogram_dict[key]; });
  //  window.my_chart.data.datasets[0].label = "Epoch number #";
  // Slowly rotate the graph, just for fun:
  pie_config['options']['rotation'] += 3;

  window.my_chart2.update();
}


function highlight_stimuli(stimuli) {
  let stimuli_row = Math.floor(stimuli / 10);
  let stimuli_col = stimuli % 10;
  for (let col_no = 0; col_no<4; col_no++) {
    for (let row_no = 0; row_no<1; row_no++) {
      let bg = "rgba(0,0,0,0.33)";
      if ((row_no == stimuli_row) && (col_no == stimuli_col)) {
        bg = "rgba(0,0,0,1.0)";
      }
      document.getElementById("p" + row_no + col_no).style.background = bg;
    }
  }
}


function connect_to_engine() {
  ws = new ReconnectingWebSocket(socket_to_use);

  //ws.onopen = function() {
  //  // what to send to engine when client starts
  //  //ws.send(JSON.stringify({
  //  //    //.... some message the I must send when I connect ....
  //  //}));
  //};

  ws.onmessage = ({ data }) => {
    set_server_status(true);
    //console.log("raw websocket data:");
    //console.log(data);
    const event = JSON.parse(data);
    //console.log(event);
    switch (event.type) {
      case "value":
//        document.getElementById("the_value").innerHTML = event.value;
        break;
//      case "eeg":
//        document.getElementById("eeg").textContent = "EEG channel 1 value: " + event.value;
//        break;
      case "status":
        document.getElementById("status").textContent = event.value;
        break;
      case "next_stimuli":
        let next_stimuli = ("00" + event.value).substr(-2,2);
        stimuli_sequence.push(next_stimuli);
        highlight_stimuli(event.value);
        document.getElementById("stimuli_sequence").innerHTML += " " + next_stimuli + ",";
        document.getElementById("nof_shown_stimuli").innerHTML = stimuli_sequence.length;
        update_stimuli_histogram(next_stimuli);
        break;
      case "eeg_quality":
        //console.log("Got EEG_QUALITY websocket info:");
        //console.log(event.data);
        update_eeg_quality_chart(event.data);
        break;
      case "recording":
        recording_opacity=1.85;
        break;
      case "prediction":
        update_prediction_chart(event.data);
        break;
      case "eeg_status":
        //console.log("Got eeg_status websocket info:");
        //console.log(event);
        // Just do nothing right now...
        break;
      case "graph":
        document.getElementById("graph").src = (event.filename) + "?cache_buster=" + Math.random();
        break;
      case "users":
        const users = `${event.count} client${event.count == 1 ? "" : "s"}`;
        document.getElementById("nof_clients").innerHTML = users;
        document.querySelector(".users").textContent = users;
        break;
      case "eeg_data":
        // Just do nothing right now...
        break;
      default:
        console.log("unsupported event", event);
    }
  };

  ws.onerror = function(err) {
    console.error('Engine gone. Reconnecting...');
    set_server_status(false);
  };
}

function calibrateAudioDisplay () {
  // Not much to do here more than telling the client through engine to start outputting latency calibration sounds + visuals
  if (server_is_up_and_running == true) {
    try {
      ws.send(JSON.stringify({ action: "calibrate", timestamp: Date.now(), what: "Audio_vs_Display"}));
    } catch {}
  }
}
function calibrateEEGAudio () {
  // Not much to do here more than telling the client through engine to start outputting latency calibration sounds
  if (server_is_up_and_running == true) {
    try {
      ws.send(JSON.stringify({ action: "calibrate", timestamp: Date.now(), what: "EEG_vs_Audio"}));
    } catch {}
  }
}
function calibrateEEGVideo () {
  // Not much to do here more than telling the client through engine to start outputting latency calibration visuals
  if (server_is_up_and_running == true) {
    try {
      ws.send(JSON.stringify({ action: "calibrate", timestamp: Date.now(), what: "EEG_vs_Display"}));
    } catch {}
  }
}

function init() {
  document.getElementById("header").style.background = "#800000";
  document.getElementById("header").style.color = "#9e4a4a";
  document.getElementById("header").style.opacity = 1.0;

  document.addEventListener('keydown', function(event) {
    console.log(event.code);
    if (event.code == 'KeyF') {
      goFullscreen();
    } else if (event.code == 'KeyA') {
      start_session();
    } else if (event.code == 'KeyS') {
      stop_session();
      return false;
    } else if (event.code == 'KeyC') {
      cancel_session();
    }
  })

  connect_to_engine();
  init_stimuli_histogram();
  document.querySelector(".poll").addEventListener("click", () => {
    ws.send(JSON.stringify({ action: "poll" }));
  });
  init_eeg_quality_chart();
  update_eeg_quality_chart({"CP3":1430.321234,"C3":2430.321234,"F5":7430.321234,"PO3":7430.321234,"PO4":7430.321234,"F6":7430.321234,"C4":7430.321234,"CP4":7430.321234});
  init_prediction_chart();
  update_prediction_chart({'hat':0.1,'tie':0.2,'briefcase':0.3,'skirt':0.4,'yellow':0.5,'blue':0.6,'green':0.7,'red':0.8,'child':0.9});

  animate(0);
}

window.addEventListener("DOMContentLoaded", () => {
  init();
});
