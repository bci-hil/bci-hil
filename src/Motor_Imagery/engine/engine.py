#!/usr/bin/env python

import os
import asyncio
import json
import logging
import websockets
import datetime
import threading
import ctypes
import pylsl
import struct
import sys
import functools
import time
import numpy as np
import mne
import matplotlib as plt
import random
import math
import re
import janus
import signal

session_log_filename = "session_log.txt"
trial_no = 0
trial_is_running = False
END_PROGRAM = False

# For printing to the console:
logging.basicConfig(level=logging.INFO)  # DEBUG / INFO / WARNING / ERRROR
#logging.basicConfig(filename='example.log', encoding='utf-8', level=logging.DEBUG)

# We need a lock for taking care of threaded asynchronous accesses to anything related to the log file and memory:
log_lock = threading.Lock()
# The in-memory version of the log:
log = []
now = str(datetime.datetime.now())

# We need a lock for taking care of threaded asynchronous accesses to the collected EEG data:
EEG_data_lock = threading.Lock()

# The websockets for communication with CLIENTs, ADMINs and COMPUTEs:
ADMINS = set()
CLIENTS = set()
COMPUTES = set()

def log_marker (marker_id, ts):
  global EEG_data_lock, log_lock
  with EEG_data_lock:
    local_clock = pylsl.local_clock()
    not_yet_written_marker_timestamps.append(local_clock)
    not_yet_written_marker_LSL_timestamps.append(ts)
    not_yet_written_marker.append(marker_id)
  with log_lock:
    now = str(datetime.datetime.now())
    row = "T%04d_marker marker_id=%d ts=%s date='%s'\n" % (trial_no, marker_id, ts, now)
    log.append(row)
    print(row)
    with open(session_log_filename, 'a') as f:
      ok = f.write(row)


trial_is_started_and_first_EEG_not_yet_received = False
trial_is_started_and_user_no = -1

def start_trial (user_no, timestamp):
  global trial_no, trial_is_running, EEG_data_lock, trial_is_started_and_first_EEG_not_yet_received, trial_is_started_and_user_no
  with log_lock:
    now = str(datetime.datetime.now())
    trial_no += 1
    row = "T%04d_start @%04d timestamp=%s date='%s'\n" % (trial_no, user_no, timestamp, now)
    log.append(row)
    print(row)
    # Append this to the session log file
    with open(session_log_filename, 'a') as f:
      ok = f.write(row)
  with EEG_data_lock:
    collected_EEG_timestamps = []
    collected_EEG_LSL_timestamps = []
    collected_EEG_time_corrections = []
    collected_EEG = []
    not_yet_written_EEG_timestamps = []
    not_yet_written_EEG_LSL_timestamps = []
    not_yet_written_EEG_time_corrections = []
    not_yet_written_EEG = []
    not_yet_written_marker_timestamps = []
    not_yet_written_marker_LSL_timestamps = []
    not_yet_written_marker = []
  trial_is_started_and_first_EEG_not_yet_received = True
  trial_is_started_and_user_no = user_no
  trial_is_running = True

def stop_trial (timestamp):
  global trial_no, log_lock
  with log_lock:
    now = str(datetime.datetime.now())
    row = "T%04d_stop timestamp=%s date='%s'\n" % (trial_no, timestamp, now)
    log.append(row)
    print(row)
    # Append this to the session log file
    with open(session_log_filename, 'a') as f:
      ok = f.write(row)

def end_trial (timestamp, correct_category):
  global trial_no, trial_is_running, log_lock
  with log_lock:
    now = str(datetime.datetime.now())
    row = "T%04d_end correct_category='%s' timestamp=%s date='%s'\n" % (trial_no, correct_category, timestamp, now)
    log.append(row)
    print(row)
    # Append this to the session log file
    with open(session_log_filename, 'a') as f:
      ok = f.write(row)
  trial_is_running = False


not_yet_written_marker = []
not_yet_written_marker_timestamps = []
not_yet_written_marker_LSL_timestamps = []
collected_EEG = []
collected_EEG_timestamps = []
collected_EEG_LSL_timestamps = []
collected_EEG_time_corrections = []
not_yet_written_EEG = []
not_yet_written_EEG_timestamps = []
not_yet_written_EEG_LSL_timestamps = []
not_yet_written_EEG_time_corrections = []
current_EEG = []
current_EEG_timestamp = 0
not_yet_sent_to_client_EEG = []
EEG_samplerate = 256

def read_doubles_from_disk(filename):
  np_array = np.fromfile(filename, dtype=np.float64)
  return np_array.tolist()

def read_floats_from_disk(filename):
  np_array = np.fromfile(filename, dtype=np.float32)
  return np_array.tolist()

def load_EEG_from_disk(from_trial_no):
  global collected_EEG, collected_EEG_timestamps, collected_EEG_time_corrections, collected_EEG_LSL_timestamps
  EEG_filename = "data/T%04d_EEG.bin" % from_trial_no
  EEG_timestamps_filename = "data/T%04d_EEG_timestamps.bin" % from_trial_no
  EEG_LSL_timestamps_filename = "data/T%04d_EEG_LSL_timestamps.bin" % from_trial_no
  EEG_time_corrections_filename = "data/T%04d_EEG_time_corrections.bin" % from_trial_no
  collected_EEG = read_doubles_from_disk(EEG_filename)
  collected_EEG_timestamps = read_doubles_from_disk(EEG_timestamps_filename)
  collected_EEG_LSL_timestamps = read_doubles_from_disk(EEG_LSL_timestamps_filename)
  collected_EEG_time_corrections = read_doubles_from_disk(EEG_time_corrections_filename)
  logging.info("Nof loaded EEG samples is %d" % len(collected_EEG_timestamps))

def write_EEG_to_disk():
  global trial_no, not_yet_written_EEG, not_yet_written_EEG_timestamps, not_yet_written_EEG_time_corrections, not_yet_written_EEG_LSL_timestamps
  logging.debug("Writing EEG to disk at %s" % datetime.datetime.now())
  EEG_filename = "data/T%04d_EEG.bin" % trial_no
  EEG_timestamps_filename = "data/T%04d_EEG_timestamps.bin" % trial_no
  EEG_LSL_timestamps_filename = "data/T%04d_EEG_LSL_timestamps.bin" % trial_no
  EEG_time_corrections_filename = "data/T%04d_EEG_time_corrections.bin" % trial_no
  with open(EEG_filename, 'ab') as f:
    ok = f.write(struct.pack('<%sd' % len(not_yet_written_EEG),*not_yet_written_EEG))
  not_yet_written_EEG = []
  with open(EEG_timestamps_filename, 'ab') as f:
    ok = f.write(struct.pack('<%sd' % len(not_yet_written_EEG_timestamps),*not_yet_written_EEG_timestamps))
  not_yet_written_EEG_timestamps = []
  with open(EEG_LSL_timestamps_filename, 'ab') as f:
    ok = f.write(struct.pack('<%sd' % len(not_yet_written_EEG_LSL_timestamps),*not_yet_written_EEG_LSL_timestamps))
  not_yet_written_EEG_LSL_timestamps = []
  with open(EEG_time_corrections_filename, 'ab') as f:
    ok = f.write(struct.pack('<%sd' % len(not_yet_written_EEG_time_corrections),*not_yet_written_EEG_time_corrections))
  not_yet_written_EEG_time_corrections = []
  # Tell the admin GUI that weäve recorded EEG data:
  send_to_admins(json.dumps({"type": "recording"}))

def write_marker_to_disk():
  global trial_no, not_yet_written_marker, not_yet_written_marker_timestamps, not_yet_written_marker_LSL_timestamps
  logging.debug("Writing marker to disk at %s" % datetime.datetime.now())
  marker_filename = "data/T%04d_marker.bin" % trial_no
  marker_timestamps_filename = "data/T%04d_marker_timestamps.bin" % trial_no
  marker_LSL_timestamps_filename = "data/T%04d_marker_LSL_timestamps.bin" % trial_no
  with open(marker_filename, 'ab') as f:
    ok = f.write(struct.pack('<%sd' % len(not_yet_written_marker),*not_yet_written_marker))
  not_yet_written_marker = []
  with open(marker_timestamps_filename, 'ab') as f:
    ok = f.write(struct.pack('<%sd' % len(not_yet_written_marker_timestamps),*not_yet_written_marker_timestamps))
  not_yet_written_marker_timestamps = []
  with open(marker_LSL_timestamps_filename, 'ab') as f:
    ok = f.write(struct.pack('<%sd' % len(not_yet_written_marker_LSL_timestamps),*not_yet_written_marker_LSL_timestamps))
  not_yet_written_marker_LSL_timestamps = []


def lsl_thread(name):
  global END_PROGRAM, trial_is_running, trial_no, not_yet_sent_to_client_EEG, not_yet_written_EEG, not_yet_written_EEG_timestamps, not_yet_written_EEG_time_corrections, not_yet_written_EEG_LSL_timestamps, trial_is_started_and_first_EEG_not_yet_received, trial_is_started_and_user_no
  try:
    # first resolve an EEG stream on the lab network
    logging.info("### Looking for LSL EEG streams from nearby devices at %s" % datetime.datetime.now())

    # As of now you can't specify a timeout which means a python program can get stuck indefinitely if no stream is found.
    streams = pylsl.resolve_stream('type', 'EEG')
    if len(streams) > 1:
      logging.warning('### Number of EEG streams is > 1, picking the first one.')
    elif len(streams) == 1:
      logging.info('### Found the EEG stream.')

    info = streams[0]
    # create a new inlet to read from the stream
    #proc_flags = 0  # Marker events are relatively rare. No need to post-process.
    #proc_flags = pysls.proc_clocksync | pylsl.proc_dejitter | pylsl.proc_monotonize
    proc_flags = pylsl.proc_clocksync | pylsl.proc_dejitter
    inlet = pylsl.StreamInlet(info, max_buflen=1, processing_flags=proc_flags)

    logging.info('### pylsl streamInfo:')
    logging.info("LSL stream name %s", info.name())
    logging.info("LSL hostname %s", info.hostname())
    logging.info("LSL stream channel count %d", info.channel_count())
    logging.info("LSL time correction %s", inlet.time_correction())
    logging.info("LSL stream created at %s", info.created_at())
    EEG_samplerate = info.nominal_srate()
    logging.debug("LSL info as xml %s", info.as_xml())
    log_string = "LSL_name=%s,LSL_hostname=%s,LSL_nof_channels=%d,LSL_created_at=%s,LSL_time_correction=%s" % (info.name(), info.hostname(), info.channel_count(), info.created_at(), inlet.time_correction())
    with log_lock:
      row = str(trial_no) + " " + now + " " + log_string + "\n"
      log.append(row)
      with open(session_log_filename, 'a') as f:
        ok = f.write(row)
    logging.info("Wrote session info to log: %s" % log_string)

    while END_PROGRAM == False:
      sample, timestamp = inlet.pull_sample()
      # Push eeg_data to CLIENTS:
      if (len(not_yet_sent_to_client_EEG) >= 1024):
        # Just flush it if nobody is listening:
        not_yet_sent_to_client_EEG = []
      not_yet_sent_to_client_EEG.extend(sample)
      local_clock = pylsl.local_clock()
      # Time correctiong will change approximately once per second, but only very little
      time_correction = inlet.time_correction()

      # We're only interested in storing EEG signals if we have an ongoing trial:
      if trial_is_running == True:
        if trial_is_started_and_first_EEG_not_yet_received == True:
          trial_is_started_and_first_EEG_not_yet_received = False
          # Save a marker with the same timestamp as the initial EEG, to be able to sync them:
          log_marker(trial_is_started_and_user_no + 4000, timestamp - time_correction)
        with EEG_data_lock:
          collected_EEG_timestamps.append(local_clock)
          collected_EEG_LSL_timestamps.append(timestamp)
          collected_EEG_time_corrections.append(time_correction)
          collected_EEG.extend(sample)
          not_yet_written_EEG_timestamps.append(local_clock)
          not_yet_written_EEG_LSL_timestamps.append(timestamp)
          not_yet_written_EEG_time_corrections.append(time_correction)
          not_yet_written_EEG.extend(sample)
          if len(not_yet_written_EEG_timestamps) > 256:
            write_EEG_to_disk()
            write_marker_to_disk()
      else:
        if len(not_yet_written_EEG_timestamps) > 0:
          with EEG_data_lock:
            write_EEG_to_disk()
            print("Flushed the EEG data at the end of a trial\n")
        if len(not_yet_written_marker_timestamps) > 0:
          with EEG_data_lock:
            write_marker_to_disk()
            print("Flushed the markers at the end of a trial\n")
    logging.info("### Ending LSL thread at %s" % datetime.datetime.now())
    logging.info("### Writing last EEG samples to disk at %s" % datetime.datetime.now())
    with EEG_data_lock:
      write_EEG_to_disk()
      write_marker_to_disk()
  except KeyboardInterrupt as e:
    logging.info("### Ending LSL thread at %s" % datetime.datetime.now())
    raise e


def lsl_thread_2(name):
  global END_PROGRAM, trial_is_running, trial_no
  try:
    # first resolve an EEG stream on the lab network
    logging.info("### Looking for LSL2 ml_results Marker streams at %s" % datetime.datetime.now())

    # As of now you can't specify a timeout which means a python program can get stuck indefinitely if no stream is found.
    streams = pylsl.resolve_byprop('name', 'ml_results')
    if len(streams) > 1:
      logging.warning('### Number of ml_results Marker streams is > 1, picking the first one.')
    elif len(streams) == 1:
      logging.info('### Found the ml_results stream.')

    info = streams[0]
    # create a new inlet to read from the stream
    proc_flags = pylsl.proc_clocksync | pylsl.proc_dejitter
    inlet2 = pylsl.StreamInlet(info, max_buflen=1, processing_flags=proc_flags)

    logging.info('### pylsl2 streamInfo:')
    logging.info("LSL2 stream name %s", info.name())
    logging.info("LSL2 hostname %s", info.hostname())
    logging.info("LSL2 stream channel count %d", info.channel_count())
    logging.info("LSL2 time correction %s", inlet2.time_correction())
    logging.info("LSL2 stream created at %s", info.created_at())

    logging.debug("LSL2 info as xml %s", info.as_xml())
    while END_PROGRAM == False:
      logging.info("### Pulling ml_results sample at %s" % datetime.datetime.now())
      sample, timestamp = inlet2.pull_sample()
      local_clock = pylsl.local_clock()
      # Time correctiong will change approximately once per second, but only very little
      time_correction = inlet2.time_correction()   # -1642543235.8716614

      # Push eeg_quality to CLIENTS and ADMINS:
      if (sample[0] == "variance"):
        dict_to_send = json.loads(sample[1])
        send_to_admins(json.dumps({"type": "eeg_quality", "data":dict_to_send}))
      elif (sample[0] == "predictions"):
        dict_to_send = json.loads(sample[1])
        send_to_admins(json.dumps({"type": "prediction", "data":dict_to_send}))
        print("Prediction from calculate: ", sample[1])
      
      elif (sample[0] == "status_fitting"):
        dict_to_send = json.loads(sample[1])
        send_to_admins(json.dumps({"type": "status_fitting", "data":dict_to_send}))

        # Set new status based on what we want to do after fitting model. 3 corresponds to READY.
        if int(sample[1]) == 1:
          print("Fitting ongoing...")
        if int(sample[1]) == 2:
          print("Fitting ready, move to status READY.")
          ts = time.time() #convert from ms to s to match time.time() format
          LSLOutletStatus.push_sample(["status", str(3)], ts)

    logging.info("### Ending LSL2 thread at %s" % datetime.datetime.now())
  except KeyboardInterrupt as e:
    logging.info("### Ending LSL2 thread at %s" % datetime.datetime.now())
    raise e


def setup_lsl_outlet(name):

  # Create LSL StreamInfo object
  lsl_StreamInfo = pylsl.StreamInfo(
                                  name=name,
                                  type="Markers",
                                  channel_count=2,
                                  nominal_srate=0,
                                  channel_format="string",
                                  source_id="GameEngine")
  channel_names=["label", "data"]
  ch_units={"label":"misc","data":"misc"}
  ch_types={"label":"marker","data":"marker"}

  # Set names on the chanels
  chns = lsl_StreamInfo.desc().append_child("channels")
  for label in channel_names:
      ch = chns.append_child("channel")
      ch.append_child_value("label", label)
      ch.append_child_value("unit", ch_units[label]) # Is this correct value?
      ch.append_child_value("type", ch_types[label]) # Is this correct value?

  # Create outlet
  return pylsl.StreamOutlet(lsl_StreamInfo)


VALUE = 0
LSLOutletMarkers = setup_lsl_outlet("MarkerStream") 
LSLOutletStatus = setup_lsl_outlet("AdminStatusStream") # TODO, replace status lsl-communication with websocket. 


def users_event():
  return json.dumps({"type": "users", "count": len(CLIENTS)})

def value_event():
  return json.dumps({"type": "value", "value": VALUE})

def eeg_event():
  return json.dumps({"type": "eeg", "eeg": current_EEG[0]})

def plot_graph_event():
  logging.info("### Plotting graph")
  graph_filename = "graph.png"

  seconds_to_use = 2.0
  nof_samples_to_use = int(seconds_to_use * EEG_samplerate)
  if len(collected_EEG_timestamps) < (nof_samples_to_use):
    logging.warning("Not enough EEG data to make a plot")
    return ""
  # Create a numpy buffer of the last X seconds of EEG:
  with EEG_data_lock:
    nof_samples = len(collected_EEG_timestamps)
    start_sample = nof_samples - nof_samples_to_use - int(100 * random.random())
    #start_sample = nof_samples - nof_samples_to_use
    logging.info("nof_samples=%d" % nof_samples)
    the_EEG = collected_EEG[(8*(start_sample)):(8*(start_sample + nof_samples_to_use))]
    the_EEG_timestamps = collected_EEG_timestamps[(start_sample):(start_sample + nof_samples_to_use)]
    the_EEG_LSL_timestamps = collected_EEG_LSL_timestamps[(start_sample):(start_sample + nof_samples_to_use)]
    the_EEG_time_corrections = collected_EEG_time_corrections[(start_sample):(start_sample + nof_samples_to_use)]

  #3. Create a numpy buffer with the EEG data
  # The correct unit for mne is volts.
  # the Crown is giving us EEG measurements in nV, so multiply by 1e-9

  # This is the wrong way around:
  the_EEG_np = np.asarray(the_EEG).reshape((nof_samples_to_use,8)) * 1e-9
  the_EEG_np = the_EEG_np.T

  the_EEG_timestamps_np = np.asarray(the_EEG_timestamps)
  the_EEG_LSL_timestamps_np = np.asarray(the_EEG_LSL_timestamps)
  the_EEG_time_corrections_np = np.asarray(the_EEG_time_corrections)

  channel_labels = ["CP3", "C3", "F5", "PO3", "PO4", "F6", "C4", "CP4"]
  logging.info("the_EEG_np shape %dx%d" % np.shape(the_EEG_np))
  logging.info("the_EEG_timestamps_np shape %d" % np.shape(the_EEG_timestamps_np))

  # Create MNE info for the data we have
  # https://mne.tools/0.23/generated/mne.create_info.html#mne.create_info
  mne_info = mne.create_info(channel_labels, EEG_samplerate, ch_types='eeg', verbose=True)

  #Then create a raw off your info and data
  raw = mne.io.RawArray(data=the_EEG_np, info=mne_info, copy='both', verbose=True)
  logging.info(raw)
  the_graph = mne.viz.plot_raw_psd(raw, fmin=0, fmax=128.0, tmin=None, tmax=None, proj=False, n_fft=None, n_overlap=0, reject_by_annotation=True, color='black', xscale='linear', area_mode='std', area_alpha=0.33, dB=True, estimate='auto', show=False, n_jobs=1, average=False, line_alpha=None, spatial_colors=True, sphere=None, window='hamming', exclude='bads', verbose=None)

  the_graph.savefig(graph_filename)

  return json.dumps({"type": "graph", "filename": "../server/%s" % graph_filename})


# Admin websocket implementation, inspired by
# https://websockets.readthedocs.io/en/stable/howto/patterns.html
admin_queue = False

async def admin_consumer_handler(websocket):
  global ADMINS, LSLOutletStatus, VALUE
  try:
    # We come here when a new client is connecting:
    print("admin client connecting")
    ADMINS.add(websocket)
    # Send current state to user:
    await websocket.send(users_event())
    await websocket.send(value_event())
    # Manage state changes
    async for message in websocket:
      # When a message is received from a admin client:
      logging.debug("admin_io")
      event = json.loads(message)
      if event["action"] == "minus":
        VALUE -= 1
        send_to_clients(value_event())
        send_to_admins(value_event())
      elif event["action"] == "plus":
        VALUE += 1
        send_to_clients(value_event())
        send_to_admins(value_event())
      elif event["action"] == "calibrate":
        # These are the current calibration types:
        #ws.send(JSON.stringify({ action: "calibrate", timestamp: Date.now(), what: "Audio_vs_Display"}));
        #ws.send(JSON.stringify({ action: "calibrate", timestamp: Date.now(), what: "EEG_vs_Audio"}));
        #ws.send(JSON.stringify({ action: "calibrate", timestamp: Date.now(), what: "EEG_vs_Display"}));
        send_to_clients(json.dumps({"type": "calibrate", "what": event["what"]}))
         # Push LSL marker to outlet.
        log_marker(998, event["timestamp"])
        logging.info(event)
        ts = event["timestamp"]/1000.0 #convert from ms to s to match time.time() format
        LSLOutletMarkers.push_sample([event["action"],repr(998)], ts)
        # And we need to start recording samples to disk as well:
        start_trial(998, event['timestamp'])
      elif event["action"] == "start":
        init_stimuli()
        # Select the stimuli_no to show next in the client:
        stimuli_no = get_next_stimuli()
        send_to_clients(json.dumps({"type": "next_stimuli", "value": stimuli_no}))
        send_to_admins(json.dumps({"type": "next_stimuli", "value": stimuli_no}))
        send_to_clients(json.dumps({"type": "trial_mode"}))
        send_to_admins(json.dumps({"type": "trial_mode"}))
         # Push LSL marker to outlet:
        logging.info(event)
        ts = event["timestamp"]/1000.0 #convert from ms to s to match time.time() format
        LSLOutletMarkers.push_sample([event["action"],repr(event['user_no'])], ts)
        start_trial(event['user_no'], event['timestamp'])
        # This marker is sent when the first EEG is registered, to keep them in sync. So don't send it yet:
        log_marker(event['user_no'], event["timestamp"])
      elif event["action"] == "stop":
        send_to_clients(json.dumps({"type": "stop_mode"}))
        logging.info(event)
        ts = event["timestamp"]/1000.0 #convert from ms to s to match time.time() format
        LSLOutletMarkers.push_sample([event["action"],repr(3000)], ts)
        log_marker(3000, event["timestamp"])
        stop_trial(event['timestamp'])
      elif event["action"] == "cancel":
        send_to_clients(json.dumps({"type": "attract_mode"}))
        send_to_admins(json.dumps({"type": "attract_mode"}))
        logging.info(event)
        ts = event["timestamp"]/1000.0 #convert from ms to s to match time.time() format
        LSLOutletMarkers.push_sample([event["action"],repr(9999)], ts)
        log_marker(9999, event["timestamp"])
        end_trial(event['timestamp'], 999)
        with EEG_data_lock:
          write_marker_to_disk()
          print("Flushed the markers at the end of a trial\n")
      elif event["action"] == "pling":
        logging.debug("### pling from admin")  
      elif event["action"] == "accumulate":
         # Push LSL marker to outlet.
        logging.info(event)
        ts = event["timestamp"]/1000.0 #convert from ms to s to match time.time() format
        LSLOutletStatus.push_sample(["status", str(1)], ts)
        #LSLOutletStatus.push_sample(["status", event["action"]], ts) 
        send_to_computes(json.dumps({"type": "status", "value": str(1),"timestamp": ts}))
      elif event["action"] == "start_fitting":
         # Push LSL marker to outlet.
        logging.info(event)
        ts = event["timestamp"]/1000.0 #convert from ms to s to match time.time() format
        LSLOutletStatus.push_sample(["status", str(2)], ts)
        #LSLOutletStatus.push_sample(["status", event["action"]], ts)
        send_to_computes(json.dumps({"type": "status", "value": str(2),"timestamp": ts}))
      elif event["action"] == "set_user_no":
         # Push LSL marker to outlet.
        logging.info(event)
        ts = event["timestamp"]/1000.0 #convert from ms to s to match time.time() format
        LSLOutletMarkers.push_sample([event["action"],repr(event['user_no'])], ts)
        send_to_computes(json.dumps({"type": "status", "value": str(2),"timestamp": ts}))
      else:
        logging.error("unsupported event: %s", event)
  finally:
    # When the client is shut down:
    ADMINS.remove(websocket)
    send_to_clients(users_event())
    send_to_admins(users_event())

def send_to_admins(json_message):
  global admin_queue
  if admin_queue != False:
    admin_queue.sync_q.put(json_message)

async def admin_producer_handler(websocket):
  global admin_queue
  try:
    while True:
      message = await admin_queue.async_q.get()
      websockets.broadcast(ADMINS, message)
  finally:
    print("Got Error:")
    print(websocket)

async def admin_io(websocket):
  # We get here when javascript connects to the admin websocket.
  admin_consumer_task = asyncio.create_task(admin_consumer_handler(websocket))
  admin_producer_task = asyncio.create_task(admin_producer_handler(websocket))
  done, pending = await asyncio.wait(
    [admin_consumer_task, admin_producer_task],
    return_when=asyncio.FIRST_COMPLETED,
  )
  for task in pending:
    task.cancel()
  logging.info("### Think admin server ended at %s" % datetime.datetime.now())

async def admin_server():
  global admin_queue
  # Set the stop condition when receiving SIGTERM.
  print(f"admin_thread Thread: {threading.get_ident()}, event loop: {id(asyncio.get_running_loop())}")
  admin_loop = asyncio.get_running_loop()
  the_admin_queue: janus.Queue[int] = janus.Queue()
  admin_queue = the_admin_queue
  stop = admin_loop.create_future()
  #admin_loop.add_signal_handler(signal.SIGTERM, stop.set_result, None)
  async with websockets.serve(admin_io, "localhost", 6581):
    logging.info("### Setup think admin server at %s" % datetime.datetime.now())
    await stop
    #await asyncio.Future()  # run forever
  logging.info("### Ending think admin server at %s" % datetime.datetime.now())

def admin_thread():
  global admin_queue
  # https://stackoverflow.com/questions/31623194/asyncio-two-loops-for-different-i-o-tasks
  print(f"admin_server Thread: {threading.get_ident()}")
  admin_loop = asyncio.new_event_loop()
  asyncio.set_event_loop(admin_loop)
  admin_loop.run_until_complete(admin_server())
  logging.info("### Ending think admin thread at %s" % datetime.datetime.now())


# Client websocket implementation, inspired by
# https://websockets.readthedocs.io/en/stable/howto/patterns.html
client_queue = False

async def client_consumer_handler(websocket):
  global CLIENTS, VALUE, COMPUTES, LSLOutletMarkers, not_yet_sent_to_client_EEG, collected_EEG_timestamps
  try:
    # We come here when a new client is connecting:
    print("client client connecting")
    CLIENTS.add(websocket)
    # Send current state to user:
    await websocket.send(users_event())
    await websocket.send(value_event())
    # Manage state changes
    async for message in websocket:
      # When a message is received from a game client:
      logging.debug("game_io")
      event = json.loads(message)
      if event["action"] == "minus":
        VALUE -= 1
        send_to_clients(value_event())
        send_to_admins(value_event())
      elif event["action"] == "plus":
        VALUE += 1
        send_to_clients(value_event())
        send_to_admins(value_event())
      elif event["action"] == "poll":
        if len(not_yet_sent_to_client_EEG) > 0:
          EEG_to_send = not_yet_sent_to_client_EEG
          not_yet_sent_to_client_EEG = []
          the_json = json.dumps({"type": "eeg_data", "sample":EEG_to_send})
          send_to_clients(the_json)
          send_to_admins(the_json)
          # Push eeg_status data to ADMINS:
          send_to_admins(json.dumps({"type": "eeg_status", "nof_eeg_samples": len(collected_EEG_timestamps)}))
        #event = plot_graph_event();
        #send_to_clients(poll_event(event))
      elif event["action"] == "show":
        # The subject now started to look at the stimuli we setup before.
        # Push LSL marker to outlet.
        logging.info(event)
        ts = event["timestamp"]/1000.0 #convert from ms to s to match time.time() format
        LSLOutletMarkers.push_sample([event["action"],repr(event["marker_id"])], ts)
        log_marker(event["marker_id"], event["timestamp"])
        # Select the stimuli_no to show next in the client:
        stimuli_no = get_next_stimuli()
        send_to_clients(json.dumps({"type": "next_stimuli", "value": stimuli_no}))
        send_to_admins(json.dumps({"type": "next_stimuli", "value": stimuli_no}))
      elif event["action"] == "show_calibrate":
        # The subject now sees a calibration text, and should tap the eeg headset in sync with these 4 events.
        # Push LSL marker to outlet.
        logging.info(event)
        ts = event["timestamp"]/1000.0 #convert from ms to s to match time.time() format
        LSLOutletMarkers.push_sample([event["action"],repr(event["marker_id"])], ts)
        log_marker(event["marker_id"], event["timestamp"])
      elif event["action"] == "end_calibrate":
        # The client has ended calibration, and we can stop recording EEG to disk now.
        print("### End calibrate!")
        end_trial(event['timestamp'], 998)
      elif event["action"] == "unshow":
        # The client just removed the previous stimuli.
        stimuli_no = get_next_stimuli()
        # Push LSL marker to outlet.
        logging.info(event)
        ts = event["timestamp"]/1000.0 #convert from ms to s to match time.time() format
        LSLOutletMarkers.push_sample(["unshow",repr(event["marker_id"])], ts)
        log_marker(event["marker_id"], event["timestamp"])
        pass
      elif event["action"] == "pause":
        # The subject needs to blink
        # Push LSL marker to outlet.
        logging.info(event)
        ts = event["timestamp"]/1000.0 #convert from ms to s to match time.time() format
        LSLOutletMarkers.push_sample([event["action"],repr(4000)], ts)
        log_marker(4000, event["timestamp"])
        pass
      else:
        logging.error("unsupported event: %s", event)
  finally:
    # When the client is shut down:
    CLIENTS.remove(websocket)
    send_to_clients(users_event())
    send_to_admins(users_event())

def send_to_clients(json_message):
  global client_queue
  if client_queue != False:
    client_queue.sync_q.put(json_message)

async def client_producer_handler(websocket):
  global client_queue
  try:
    while True:
      message = await client_queue.async_q.get()
      websockets.broadcast(CLIENTS, message)
  finally:
    print("Got Error:")
    print(websocket)

async def client_io(websocket):
  # We get here when javascript connects to the client websocket.
  client_consumer_task = asyncio.create_task(client_consumer_handler(websocket))
  client_producer_task = asyncio.create_task(client_producer_handler(websocket))
  done, pending = await asyncio.wait(
    [client_consumer_task, client_producer_task],
    return_when=asyncio.FIRST_COMPLETED,
  )
  for task in pending:
    task.cancel()
  logging.info("### Think client server ended at %s" % datetime.datetime.now())

async def client_server():
  global client_queue
  # Set the stop condition when receiving SIGTERM.
  print(f"client_thread Thread: {threading.get_ident()}, event loop: {id(asyncio.get_running_loop())}")
  client_loop = asyncio.get_running_loop()
  the_client_queue: janus.Queue[int] = janus.Queue()
  client_queue = the_client_queue
  stop = client_loop.create_future()
  #client_loop.add_signal_handler(signal.SIGTERM, stop.set_result, None)
  async with websockets.serve(client_io, "localhost", 8580):
    logging.info("### Setup think client server at %s" % datetime.datetime.now())
    await stop
    #await asyncio.Future()  # run forever
  logging.info("### Ending think client server at %s" % datetime.datetime.now())

def client_thread():
  global client_queue
  # https://stackoverflow.com/questions/31623194/asyncio-two-loops-for-different-i-o-tasks
  print(f"client_server Thread: {threading.get_ident()}")
  client_loop = asyncio.new_event_loop()
  asyncio.set_event_loop(client_loop)
  client_loop.run_until_complete(client_server())
  logging.info("### Ending think client thread at %s" % datetime.datetime.now())

def poll_event(event):
  return event
  #return json.dumps({"type": "status", "value": len(collected_EEG_timestamps)})


# Compute websocket implementation, inspired by
# https://websockets.readthedocs.io/en/stable/howto/patterns.html
compute_queue = False

async def compute_consumer_handler(websocket):
  global COMPUTES, VALUE, COMPUTES, LSLOutletMarkers
  try:
    # We come here when a new compute is connecting:
    print("compute connecting")
    COMPUTES.add(websocket)
    send_to_admins(users_event())
    send_to_clients(users_event())
    send_to_computes(users_event())
    # Send current state to user
    await websocket.send(value_event())
    # Manage state changes
    async for message in websocket:
      # When a message is received from a admin client:
      logging.debug("compute_io")
      event = json.loads(message)
      if event["action"] == "minus":
        VALUE -= 1
        send_to_admins(value_event())
        send_to_clients(value_event())
        send_to_computes(value_event())
      elif event["action"] == "plus":
        VALUE += 1
        send_to_admins(value_event())
        send_to_clients(value_event())
        send_to_computes(value_event())
      else:
        logging.error("unsupported event: %s", event)
  finally:
    # When the compute is shut down:
    COMPUTES.remove(websocket)
    send_to_admins(users_event())
    send_to_clients(users_event())
    send_to_computes(users_event())

def send_to_computes(json_message):
  global compute_queue
  if compute_queue != False:
    compute_queue.sync_q.put(json_message)

async def compute_producer_handler(websocket):
  global compute_queue
  try:
    while True:
      message = await compute_queue.async_q.get()
      websockets.broadcast(COMPUTES, message)
  finally:
    print("Got Error:")
    print(websocket)

async def compute_io(websocket):
  # We get here when javascript connects to the compute websocket.
  compute_consumer_task = asyncio.create_task(compute_consumer_handler(websocket))
  compute_producer_task = asyncio.create_task(compute_producer_handler(websocket))
  done, pending = await asyncio.wait(
    [compute_consumer_task, compute_producer_task],
    return_when=asyncio.FIRST_COMPLETED,
  )
  for task in pending:
    task.cancel()
  logging.info("### Think compute server ended at %s" % datetime.datetime.now())

async def compute_server():
  global compute_queue
  # Set the stop condition when receiving SIGTERM.
  print(f"compute_thread Thread: {threading.get_ident()}, event loop: {id(asyncio.get_running_loop())}")
  compute_loop = asyncio.get_running_loop()
  the_compute_queue: janus.Queue[int] = janus.Queue()
  compute_queue = the_compute_queue
  stop = compute_loop.create_future()
  #compute_loop.add_signal_handler(signal.SIGTERM, stop.set_result, None)
  async with websockets.serve(compute_io, "localhost", 7518):
    logging.info("### Setup think compute server at %s" % datetime.datetime.now())
    await stop
    #await asyncio.Future()  # run forever
  logging.info("### Ending think compute server at %s" % datetime.datetime.now())

def compute_thread():
  global compute_queue
  # https://stackoverflow.com/questions/31623194/asyncio-two-loops-for-different-i-o-tasks
  print(f"compute_server Thread: {threading.get_ident()}")
  compute_loop = asyncio.new_event_loop()
  asyncio.set_event_loop(compute_loop)
  compute_loop.run_until_complete(compute_server())
  logging.info("### Ending think compute thread at %s" % datetime.datetime.now())


def init_stimuli():
  # Actually, there's nothing to be done here
  return

def get_next_stimuli():
  return random.randint(0, 3)


if __name__ == "__main__":
  logging.info("### Think server. Press ENTER to exit")
  # Grab the session number, and increase it
  # The on-disk version of the log:
  logging.info("Reading session log from disk.")
  if os.path.exists(session_log_filename) == False:
    logging.info("Session log file '%s' does not exist. Creating it." % session_log_filename)
    with log_lock:
      row = "# Log file inited, date=%s\n" % now
      log.append(row)
      with open(session_log_filename, 'w') as f:
        ok = f.write(row)
  else:
    with log_lock:
      with open(session_log_filename, 'r') as f:
        for row in f:
          log.append(row)
          result = re.match('^T([0-9]{4})_', row)
          if result:
            trial_no = int(result.group(1))
  logging.info("There are %d rows in the trial log file '%s'." % (len(log), session_log_filename))
  logging.info("The last trial number was T%04d." % trial_no)
  # Let the LSL thread write the session information into the session log

  EEG_data_folder_name = "data"
  if os.path.exists(EEG_data_folder_name) == False:
    logging.info("### Creating a folder named '%s' for storing raw EEG data." % EEG_data_folder_name)
    os.makedirs(EEG_data_folder_name)

  if len(sys.argv) > 1:
    from_trial_no = int(sys.argv[1])
    logging.info("### Grabbing EEG data from previous session no %d" % from_trial_no)
    load_EEG_from_disk(from_trial_no)
  else:
    logging.info("### Setting up LSL thread at %s" % datetime.datetime.now())
    thread = threading.Thread(target=lsl_thread, args=(1,))
    # Thread will not prevent main function to exit. Exit anytime when thread is daemon:
    #https://www.geeksforgeeks.org/python-different-ways-to-kill-a-thread/
    thread.daemon = True
    logging.info("### Starting threads at %s" % datetime.datetime.now())
    thread.start()

    logging.info("### Setting up LSL thread 2 at %s" % datetime.datetime.now())
    thread2 = threading.Thread(target=lsl_thread_2, args=(1,))
    # Thread will not prevent main function to exit. Exit anytime when thread is daemon:
    #https://www.geeksforgeeks.org/python-different-ways-to-kill-a-thread/
    thread2.daemon = True
    logging.info("### Starting thread 2 at %s" % datetime.datetime.now())
    thread2.start()

  logging.info("### Starting websockets at %s" % datetime.datetime.now())
  ws_server_admin_thread = threading.Thread(target=admin_thread, args=(), daemon=True)
  logging.info("### Starting admin_thread at %s" % datetime.datetime.now())
  ws_server_admin_thread.start()

  ws_server_client_thread = threading.Thread(target=client_thread, args=(), daemon=True)
  logging.info("### Starting client_thread at %s" % datetime.datetime.now())
  ws_server_client_thread.start()

  ws_server_compute_thread = threading.Thread(target=compute_thread, args=(), daemon=True)
  logging.info("### Starting compute_thread at %s" % datetime.datetime.now())
  ws_server_compute_thread.start()

  logging.info("async-stuff done")
  input("\n### Press ENTER to quit\n\n")
  END_PROGRAM = True
  time.sleep(0.2)
  logging.info("### Stopping threads at %s" % datetime.datetime.now())
