'use strict';

// The client can be in these modes:
// attract:   Doing some background animations to look interesting to passing by spectators
// trial:     Displaying graphics for a subject.
// stop:     No more suspects shown to the subject, but presenting results and asking for the correct category.
let client_mode = 'attract';

// The mode in sync with animations, delays, etc. More or less a state machine that will
// try to mimic client_mode but with delays:
let client_visualization_mode = 'init';

const sunburst_div = document.getElementById("sunburst");

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



const socket_to_use = "ws://localhost:8580/";
let server_is_up_and_running = "init";
let ws;

function set_server_status(is_up) {
  if ((is_up == true) && (server_is_up_and_running == false)) {
    document.body.style.background = "none";
    document.querySelector(".users").textContent = "";
  } else if ((is_up == false) && (server_is_up_and_running == true)) {
    document.body.style.background = "#800000";
    document.querySelector(".users").textContent = "The engine isn't up and running";
    document.getElementById("timestamp").innerHTML = "";
  }
  server_is_up_and_running = is_up;
}

let update_frequency = 2.0
let nof_frames_since_last_update = 0
let last_subject = null;
let last_timestamp = -1;

function set_next_subject(which_subject) {
  console.log("Got next subject " + which_subject);
  subject_to_show = which_subject;
  if (timestamp_for_next_subject < 0) {
    // Trigger the first one immediately:
    timestamp_for_next_subject = 0;
  }
}

let interval = 0;
let nof_frames_left_visible = 0;
let subject_to_show = null;
const nof_milliseconds_subjects_are_visible = 300; //1000;
const nof_milliseconds_subject_triggered = 500; //1500;
const nof_milliseconds_subject_triggered_randomness = 200; //400;
let timestamp_for_erasing_subject = -1;
let timestamp_for_next_subject = -1;

let logo_opacity = 0.0;
let sunburst_opacity = 0.0;
let sunburst_opacity_dest = 0.4;
let suspect_animation = [];
let attract_suspect_opacity = 1.0;
let prepare_opacity = 0.0;
let countdown_plus_opacity = 0.0;
let get_ready_opacity = 0.0;
let suspect_ground_opacity = 0.0;
let introduction_opacity = 0.0;
let introduction_opacity_dest = 0.4;
let footer_opacity = 0.0;
let footer_opacity_dest = 0.4;
let calibrate_opacity = 0.0;

let nof_subjects_between_pauses = 20;
let nof_subjects_left_until_pause = 20;
let suspect_that_will_be_unshown = -1;

function animate (timestamp) {
  let milliseconds_since_last_animate = timestamp - last_timestamp;
  last_timestamp = timestamp;
  // 60 Hz screen:  8079.115  8095.795      diff = 16,68
  // 120Hz screen:  3345.732  3354.065      diff =  8,333

  if (logo_opacity < 0.3) {
    logo_opacity += 0.005 * milliseconds_since_last_animate*60/1000;
    document.getElementById('logo').style.opacity = logo_opacity;
    document.getElementById('header').style.opacity = logo_opacity * 0.25/0.3;
  }

  if (introduction_opacity != introduction_opacity_dest) {
    introduction_opacity += (introduction_opacity_dest - introduction_opacity) * 0.025;
    document.getElementById('introduction').style.opacity = introduction_opacity;
  }

  if (footer_opacity != footer_opacity_dest) {
    footer_opacity += (footer_opacity_dest - footer_opacity) * 0.025;
    document.getElementById('footer').style.opacity = footer_opacity;
  }

  if (sunburst_opacity != sunburst_opacity_dest) {
    sunburst_opacity += (sunburst_opacity_dest - sunburst_opacity) * 0.025;
    document.getElementById('sunburst').style.opacity = sunburst_opacity;
  }


  if (server_is_up_and_running == false) {
    // Just do nothing.
    sunburst_div.style.display = "none";
    document.getElementById("timestamp").innerHTML = "";
  } else if (client_visualization_mode == 'calibrate') {
    // We still want eeg_data to show in the client graphs, so let's poll it:
    try {
      ws.send(JSON.stringify({action: "poll"}));
    } catch {}
    attract_suspect_opacity = 0.0;
    sunburst_div.style.display = "none";
    document.getElementById("p00").style.opacity = 0.0;
    document.getElementById("p01").style.opacity = 0.0;
    document.getElementById("p02").style.opacity = 0.0;
    document.getElementById("p03").style.opacity = 0.0;
    document.getElementById("p04").style.opacity = 0.0;
    document.getElementById("p10").style.opacity = 0.0;
    document.getElementById("p11").style.opacity = 0.0;
    document.getElementById("p12").style.opacity = 0.0;
    document.getElementById("p13").style.opacity = 0.0;
    document.getElementById("p14").style.opacity = 0.0;
    document.getElementById("p20").style.opacity = 0.0;
    document.getElementById("p21").style.opacity = 0.0;
    document.getElementById("p22").style.opacity = 0.0;
    document.getElementById("p23").style.opacity = 0.0;
    document.getElementById("p24").style.opacity = 0.0;
    document.getElementById("p30").style.opacity = 0.0;
    document.getElementById("p31").style.opacity = 0.0;
    document.getElementById("p32").style.opacity = 0.0;
    document.getElementById("p33").style.opacity = 0.0;
    document.getElementById("p34").style.opacity = 0.0;
    document.getElementById('suspect_ground').style.opacity = 0.0;
    document.getElementById('svgdiv').style.opacity = 0.0;
    document.getElementById('prepare').style.opacity = 0.0;
    document.getElementById('countdown_plus').style.opacity = 0.0;
    document.getElementById('get_ready').style.opacity = 0.0;
    introduction_opacity_dest = 0.0;
    //console.log("calibrate_frame_no");
    //console.log(calibrate_frame_no);
    //console.log(timestamp - calibrate_from_timestamp);
    let flash_screen = "#000000";
    let flash_strobe = -1;
    calibrate_opacity -= (milliseconds_since_last_animate / 1000);
    if (calibrate_frame_no == 0) {
      calibrate_from_timestamp = timestamp;
      flash_screen = "#ffffff";
      calibrate_frame_no += 1;
      document.getElementById("calibrate").innerHTML = "";
    } else if (Math.floor(timestamp - calibrate_from_timestamp) >= (calibrate_frame_no * 500)) {
      calibrate_frame_no += 1;
      flash_strobe = calibrate_frame_no;
      flash_screen = "#ffffff";
      console.log("flash_strobe="+flash_strobe)
    }

    if (flash_strobe == 2) {
      document.getElementById("calibrate").innerHTML = "Tap";
      calibrate_opacity = 1.2;
    } else if (flash_strobe == 4) {
      document.getElementById("calibrate").innerHTML = "eight";
      calibrate_opacity = 1.2;
    } else if (flash_strobe == 6) {
      document.getElementById("calibrate").innerHTML = "times";
      calibrate_opacity = 1.2;
    } else if (flash_strobe == 8) {
      document.getElementById("calibrate").innerHTML = "now:";
      calibrate_opacity = 1.2;
    } else if ((flash_strobe >= 10) && (flash_strobe <= 17)) {
      document.getElementById("calibrate").innerHTML = String(flash_strobe + 1 - 10);
      calibrate_opacity = 0.6;
      // Tell game engine that calibration 1 is happening:
      let marker_id = 8001 + flash_strobe - 10;
      let animate_now = Date.now();
      document.getElementById("timestamp").innerHTML = animate_now.toString().substring(6) + '.8' + String(marker_id - 8000);
      if (server_is_up_and_running == true) {
        try {
          ws.send(JSON.stringify({marker_id: marker_id, timestamp: animate_now, action: "show_calibrate"}));
        } catch {}
      }
    } else if (flash_strobe == 18) {
      document.getElementById("calibrate").innerHTML = "";
      client_visualization_mode = "init";
      console.log("// Tell the engine that calibration has ended:");
      if (server_is_up_and_running == true) {
        try {
          let animate_now = Date.now();
          ws.send(JSON.stringify({marker_id: 8998, timestamp: animate_now, action: "end_calibrate"}));
        } catch {}
      }
      client_mode = "attract";
      flash_screen = "#000000";
    }
    console.log(calibrate_opacity);
    let opacity = Math.min(1.0,2.0 * calibrate_opacity);
    opacity = Math.max(0.0,opacity);
    document.getElementById("calibrate").style.opacity = opacity;
    document.getElementById("calibrate").style.background = flash_screen;
    document.body.style.backgroundColor = flash_screen;


  } else if (client_visualization_mode == 'init') {
    client_visualization_mode = 'attract';
    document.getElementById("timestamp").innerHTML = "";
    attract_suspect_opacity = 0.0;
    for (let row_no = 0; row_no<=3; row_no++) {
      for (let col_no = 0; col_no<=4; col_no++) {
        let suspect_no = row_no*10 + col_no;
        suspect_animation[suspect_no]['x'] = -30 + 130 * Math.random();
        suspect_animation[suspect_no]['top'] = 0 + 20*Math.random();
        suspect_animation[suspect_no]['x_spd'] = 0.02 + 0.04 * Math.random();
      }
    }

  } else if (client_visualization_mode == 'trial') {
    document.getElementById('countdown_plus').style.opacity = 0.0;
    document.getElementById('prepare').style.opacity = 0.0;
    document.getElementById('get_ready').style.opacity = 0.0;
    document.getElementById('svgdiv').style.opacity = 1.0;
    sunburst_opacity_dest = 0.0;
    if (sunburst_opacity < 0.01) {
      sunburst_div.style.display = "none";
    } else {
      sunburst_div.style.display = "inline";
    }
    if ((timestamp >= timestamp_for_next_subject) && (subject_to_show != null) && (client_mode == "trial")) {
      try{
        last_subject.style.opacity = 0.0;
        last_subject = null;
      } catch {}
      let subject = document.getElementById(subject_to_show);
      subject.style.width = "30%";
      subject.style.height = "100%";
      subject.style.left = "36%";
      subject.style.top = "0%";
      subject.style.opacity = 1.0;
      console.log("Showing " + subject_to_show);
      timestamp_for_erasing_subject = timestamp + nof_milliseconds_subjects_are_visible;
      timestamp_for_next_subject = timestamp + nof_milliseconds_subject_triggered + Math.random() * nof_milliseconds_subject_triggered_randomness;
      // Tell game engine that the subject is visible now:
      let marker_id = 1000 + parseInt(subject_to_show.substr(1));
      suspect_that_will_be_unshown = parseInt(subject_to_show.substr(1));
      let animate_now = Date.now();
      document.getElementById("timestamp").innerHTML = animate_now.toString().substring(6) + '.' + subject_to_show.substr(1);
      if (server_is_up_and_running == true) {
        try {
          ws.send(JSON.stringify({marker_id: marker_id, timestamp: animate_now, action: "show"}));
        } catch {}
      }
      last_subject = subject;
      subject_to_show = null;
    }

    if (timestamp >= timestamp_for_erasing_subject) {
      if (last_subject != null) {
        try{
          last_subject.style.opacity = 0.0;
          last_subject = null;
        } catch {}

        // Tell game engine that the subject is gone now:
        let marker_id = 2000 + suspect_that_will_be_unshown;
        if (server_is_up_and_running == true) {
          try {
            ws.send(JSON.stringify({marker_id: marker_id, timestamp: Date.now(), action: "unshow"}));
          } catch {}
        }

        nof_subjects_left_until_pause -= 1;
        if (nof_subjects_left_until_pause <= 0) {
          console.log("Doing pause");
          let marker_id = 4000;
          if (server_is_up_and_running == true) {
            try {
              ws.send(JSON.stringify({marker_id: marker_id, timestamp: Date.now(), action: "pause"}));
            } catch {}
          }
          nof_subjects_left_until_pause = nof_subjects_between_pauses;
          client_visualization_mode = 'going_to_trial';
          prepare_opacity = 0.0;
          countdown_plus_opacity = 4.0;
          get_ready_opacity = 6.0;
        }
      }
      // Only switch to another mode when we have removed the graphics:
      if (client_mode == 'attract') {
        client_visualization_mode = 'attract';
        // Hide all suspects:
        document.getElementById("p00").style.opacity = 0.0;
        document.getElementById("p01").style.opacity = 0.0;
        document.getElementById("p02").style.opacity = 0.0;
        document.getElementById("p03").style.opacity = 0.0;
        document.getElementById("p04").style.opacity = 0.0;
        document.getElementById("p10").style.opacity = 0.0;
        document.getElementById("p11").style.opacity = 0.0;
        document.getElementById("p12").style.opacity = 0.0;
        document.getElementById("p13").style.opacity = 0.0;
        document.getElementById("p14").style.opacity = 0.0;
        document.getElementById("p20").style.opacity = 0.0;
        document.getElementById("p21").style.opacity = 0.0;
        document.getElementById("p22").style.opacity = 0.0;
        document.getElementById("p23").style.opacity = 0.0;
        document.getElementById("p24").style.opacity = 0.0;
        document.getElementById("p30").style.opacity = 0.0;
        document.getElementById("p31").style.opacity = 0.0;
        document.getElementById("p32").style.opacity = 0.0;
        document.getElementById("p33").style.opacity = 0.0;
        document.getElementById("p34").style.opacity = 0.0;
      }
    }
  } else if (client_visualization_mode == 'attract') {
    introduction_opacity_dest = 1.0;
    footer_opacity_dest = 0.6;
    document.getElementById("timestamp").innerHTML = "";
    if (suspect_ground_opacity > 0.0) {
      suspect_ground_opacity = suspect_ground_opacity - 0.005 * milliseconds_since_last_animate*60/1000;
      document.getElementById('suspect_ground').style.opacity = suspect_ground_opacity;
    } else {
      document.getElementById('suspect_ground').style.opacity = 0.0;
    }
    sunburst_opacity_dest = 0.4;
    sunburst_div.style.display = "inline";

    if (attract_suspect_opacity < 1.0) {
      attract_suspect_opacity = attract_suspect_opacity + 0.004 * milliseconds_since_last_animate*60/1000;
      document.getElementById('svgdiv').style.opacity = attract_suspect_opacity;
    } else {
      document.getElementById('svgdiv').style.opacity = 1.0;
    }

    // Move one suspect:
    for (let row_no = 0; row_no<=3; row_no++) {
      for (let col_no = 0; col_no<=4; col_no++) {
        let suspect_no = row_no * 10 + col_no;
        suspect_animation[suspect_no]['x'] -= suspect_animation[suspect_no]['x_spd'];
        if (suspect_animation[suspect_no]['x'] < -40) {
          suspect_animation[suspect_no]['x'] = 100;
          suspect_animation[row_no*10 + col_no]['x_spd'] = 0.025 + 0.06 * Math.random();
        }
        suspect_animation[suspect_no]['element'].style.left = suspect_animation[suspect_no]['x'] + "%";
        suspect_animation[suspect_no]['element'].style.top = (8 * row_no + col_no) + "%";
        suspect_animation[suspect_no]['element'].style.width = "60%";
        suspect_animation[suspect_no]['element'].style.height = "100%";
        suspect_animation[suspect_no]['element'].style.opacity = 1.0;
      }
    }
    try {
      ws.send(JSON.stringify({action: "poll"}));
    } catch {}


    if (client_mode == 'trial') {
      client_visualization_mode = 'leaving_attract';
    }
  } else if (client_visualization_mode == 'leaving_attract') {
    sunburst_opacity_dest = 0.0;
    introduction_opacity_dest = 0.0;
    footer_opacity_dest = 0.0;
    if (suspect_ground_opacity < 0.35) {
      suspect_ground_opacity = suspect_ground_opacity + 0.01 * milliseconds_since_last_animate*60/1000;
      document.getElementById('suspect_ground').style.opacity = suspect_ground_opacity;
    }

    attract_suspect_opacity = attract_suspect_opacity - 0.015 * milliseconds_since_last_animate*60/1000;
    document.getElementById('svgdiv').style.opacity = attract_suspect_opacity;
    if (attract_suspect_opacity < 0.0) {
      client_visualization_mode = 'going_to_trial';
      prepare_opacity = 3.0;
      countdown_plus_opacity = 8.0;
      get_ready_opacity = 10.0;
      for (let row_no = 0; row_no<=3; row_no++) {
        for (let col_no = 0; col_no<=4; col_no++) {
          let suspect_no = row_no * 10 + col_no;
          suspect_animation[suspect_no]['element'].style.opacity = 0.0;
        }
      }
    } else {
      // Move one suspect:
      for (let row_no = 0; row_no<=3; row_no++) {
        for (let col_no = 0; col_no<=4; col_no++) {
          let suspect_no = row_no * 10 + col_no;
          suspect_animation[suspect_no]['x'] -= suspect_animation[suspect_no]['x_spd'];
          if (suspect_animation[suspect_no]['x'] < -40) {
            suspect_animation[suspect_no]['x'] = 100;
            suspect_animation[row_no*10 + col_no]['x_spd'] = 0.025 + 0.06 * Math.random();
          }
          suspect_animation[suspect_no]['element'].style.left = suspect_animation[suspect_no]['x'] + "%";
          suspect_animation[suspect_no]['element'].style.top = (8 * row_no + col_no) + "%";
          suspect_animation[suspect_no]['element'].style.width = "60%";
          suspect_animation[suspect_no]['element'].style.height = "100%";
          suspect_animation[suspect_no]['element'].style.opacity = 1.0;
        }
      }
    }
  } else if (client_visualization_mode == 'going_to_trial') {
    sunburst_opacity_dest = 0.0;
    prepare_opacity = prepare_opacity - milliseconds_since_last_animate / 1000;
    countdown_plus_opacity = countdown_plus_opacity - milliseconds_since_last_animate / 1000;
    get_ready_opacity = get_ready_opacity - milliseconds_since_last_animate / 1000;

    if (prepare_opacity > 1.0) {
      document.getElementById('prepare').style.opacity = 1.0;
      document.getElementById('countdown_plus').style.opacity = 1.0;
    } else if (prepare_opacity > 0.0) {
      document.getElementById('prepare').style.opacity = prepare_opacity;
    } else if (countdown_plus_opacity > 0.0) {
      document.getElementById('prepare').style.opacity = 0.0;
      document.getElementById('countdown_plus').style.opacity = countdown_plus_opacity;
    } else if (get_ready_opacity > 1.0) {
      document.getElementById('countdown_plus').style.opacity = 0.0;
      document.getElementById('get_ready').style.opacity = 1.0;
    } else if (get_ready_opacity > 0.0) {
      document.getElementById('get_ready').style.opacity = get_ready_opacity;
      document.getElementById('prepare').style.opacity = 0.0;
    } else {
      client_visualization_mode = 'trial';
      document.getElementById('get_ready').style.opacity = 0.0;
    }

    if (suspect_ground_opacity < 0.35) {
      suspect_ground_opacity = suspect_ground_opacity + 0.02 * milliseconds_since_last_animate*60/1000;
      document.getElementById('suspect_ground').style.opacity = suspect_ground_opacity;
    }
  }

  if ((webgl_is_up_and_running == true)) {
    if ((client_visualization_mode == 'attract') || (client_visualization_mode == 'calibrate')) {
      renderer.render( scene, camera );
      // Move the graphs with an expected "4 eeg samples per frame" speed to the left. Just to make them smoother.
      scroll_eeg_data(milliseconds_since_last_animate);
    } else {
      renderer.clear();
    }
  }

  window.requestAnimationFrame(animate);
}

let t = 0.0;

function clicked_plus() {
  ws.send(JSON.stringify({ action: "plus" }));
}

function clicked_minus() {
  ws.send(JSON.stringify({ action: "minus" }));
}


let calibrate_what = null;
let calibrate_frame_no = -1;
let calibrate_from_timestamp = 0;

function calibrate_latency (what) {
  // what: "Audio_vs_Display"
  // what: "EEG_vs_Audio"
  // what: "EEG_vs_Display"
  console.log("Asked to start calibrating latency for ")
  console.log(what)
  client_visualization_mode = "calibrate";
  calibrate_what = what;
  calibrate_frame_no = 0;
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
    //console.log("got ws data:" + data);
    const event = JSON.parse(data);
    //console.log(event);
    switch (event.type) {
      case "value":
        document.getElementById("the_value").innerHTML = event.value;
        break;
      case "eeg_data":
        add_new_eeg_data(event.sample);
        //console.log(event.sample);
        break;
      case "status":
        document.getElementById("status").textContent = event.value;
        break;
      case "calibrate":
        calibrate_latency(event.what);
        break;
      case "trial_mode":
        client_mode = "trial";
        break;
      case "stop_mode":
        client_mode = "stop";
        break;
      case "attract_mode":
        client_mode = "attract";
        break;
      case "next_suspect":
        let next_suspect = ("00" + event.value).substr(-2,2);
        set_next_subject("p" + next_suspect);
        break;
      case "graph":
        document.getElementById("graph").src = (event.filename) + "?cache_buster=" + Math.random();
        break;
      case "users":
        const users = `${event.count} player${event.count == 1 ? "" : "s"}`;
        document.querySelector(".users").textContent = users;
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

let eeg_data_scrolled = 0;

function add_new_eeg_data (data) {
  let nof_new_samples = Math.floor(data.length / 8);
  let samples_to_scroll = Math.max(nof_new_samples - eeg_data_scrolled, 0);
  //let eeg_data_insertion_point = eeg_data_length - eeg_data_scrolled;
  let eeg_data_insertion_point = eeg_data_length - eeg_data_scrolled - samples_to_scroll;
  //console.log("to scroll=%d, insertion point=%d", samples_to_scroll, eeg_data_insertion_point);
  for (let eeg_channel_no=0; eeg_channel_no < nof_eeg_channels; eeg_channel_no++) {
    // Move the old data:
    if (samples_to_scroll > 0) {
      for (let i=0; i<eeg_data_length - samples_to_scroll; i++) {
        uniforms[eeg_channel_no].tAudioData.value.source.data.data[i] = uniforms[eeg_channel_no].tAudioData.value.source.data.data[i + samples_to_scroll];
      }
    }
    // Add the new data:
    for (let i=0; i<nof_new_samples; i++) {
      uniforms[eeg_channel_no].tAudioData.value.source.data.data[eeg_data_insertion_point+i] = 130 + 126 * (data[eeg_channel_no + i*8] / 10000);
    }
    //console.log(uniforms[eeg_channel_no].tAudioData.value.source.data.data);
    uniforms[eeg_channel_no].tAudioData.value.needsUpdate = true;
  }
  eeg_data_scrolled += samples_to_scroll;
  eeg_data_scrolled -= nof_new_samples;
}

function scroll_eeg_data (milliseconds_since_last_animate) {
  if (eeg_data_scrolled > (eeg_data_length/2)) {
    return;
  }
  let samples_to_scroll = Math.floor(256*milliseconds_since_last_animate / 1000.0);
  for (let eeg_channel_no=0; eeg_channel_no < nof_eeg_channels; eeg_channel_no++) {
    // Move the old data:
    if (samples_to_scroll > 0) {
      for (let i=0; i<eeg_data_length - samples_to_scroll; i++) {
        uniforms[eeg_channel_no].tAudioData.value.source.data.data[i] = uniforms[eeg_channel_no].tAudioData.value.source.data.data[i + samples_to_scroll];
      }
      // Empty data that isn't here yet:
      for (let i=eeg_data_length - samples_to_scroll; i<eeg_data_length; i++) {
        uniforms[eeg_channel_no].tAudioData.value.source.data.data[i] = 0;
      }

    }
    uniforms[eeg_channel_no].tAudioData.value.needsUpdate = true;
  }
  eeg_data_scrolled += samples_to_scroll;
  return;
}

let scene, camera, renderer, analyser;

let webgl_is_up_and_running = false;
const eeg_data_length = 256;
// const nof_eeg_channels = 8; // The Crown
const nof_eeg_channels = 4; // museS
let uniforms = [];
let eeg_waveform_meshes = [];

function init_webgl () {
  const container = document.getElementById( 'container' );
  renderer = new THREE.WebGLRenderer( { antialias: true } );
  renderer.setSize( window.innerWidth, window.innerHeight );
  renderer.setClearColor( 0,0,0,0,0 );
  renderer.setPixelRatio( window.devicePixelRatio );
  container.appendChild( renderer.domElement );
  scene = new THREE.Scene();
  camera = new THREE.Camera();
  //
  const format = ( renderer.capabilities.isWebGL2 ) ? THREE.RedFormat : THREE.LuminanceFormat;
  for (let eeg_channel_no=0; eeg_channel_no < nof_eeg_channels; eeg_channel_no++) {
    let eeg_data0b = new Uint8Array(eeg_data_length);
    uniforms[eeg_channel_no] = {
      tAudioData: { value: new THREE.DataTexture( eeg_data0b, eeg_data_length, 1, format ) }
    };

    const material = new THREE.ShaderMaterial( {
      uniforms: uniforms[eeg_channel_no],
      vertexShader: document.getElementById( 'vertexShader' ).textContent,
      fragmentShader: document.getElementById( 'fragmentShader' ).textContent
    } );
    const geometry = new THREE.PlaneGeometry( 1.6/nof_eeg_channels, 0.3 );
    geometry.translate ( -0.8 + 1.8 * eeg_channel_no / nof_eeg_channels, -0.55, 0.0 );
    const mesh = new THREE.Mesh( geometry, material );
    scene.add( mesh );
    eeg_waveform_meshes[eeg_channel_no] = mesh;
  }

  //
  window.addEventListener( 'resize', onWindowResize );

  for (let i=0; i<eeg_data_length; i++) {
    uniforms[0].tAudioData.value.source.data.data[i] = 130 + 126 * Math.cos(i * 0.05 + t);
  }
  uniforms[0].tAudioData.value.needsUpdate = true;

  webgl_is_up_and_running = true;
}
function onWindowResize() {
  renderer.setSize( window.innerWidth, window.innerHeight );
}



function init() {
  connect_to_engine();

  for (let row_no = 0; row_no<=3; row_no++) {
    for (let col_no = 0; col_no<=4; col_no++) {
      let suspect_no = row_no*10 + col_no;
      suspect_animation[suspect_no] = {};
      suspect_animation[suspect_no]['element'] = document.getElementById("p" + row_no + col_no);
    }
  }

  document.addEventListener('keydown', function(event) {
    if (event.code == 'KeyF') {
      goFullscreen();
    }
  })

  document.querySelector(".poll").addEventListener("click", () => {
    ws.send(JSON.stringify({ action: "poll" }));
  });
  set_next_subject("p00");
  init_webgl();

  animate(0);
}

window.addEventListener("DOMContentLoaded", () => {
  init();
});
