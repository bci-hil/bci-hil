"""Machine Learning"""

import importlib
import glob
import json
from jsonschema import validate
from re import A
from datetime import datetime
import os
from pathlib import Path
import pickle
from time import time

import numpy as np
import pandas as pd
from pyriemann.estimation import Covariances

from timeflux.core.node import Node
from timeflux.helpers.port import make_event, match_events, get_meta
from timeflux.nodes_dev.helpers import get_data, get_dict_keys_by_start

from pylsl import StreamInfo, StreamOutlet, StreamInlet, resolve_byprop

# Use to import from sibling folder
import sys
sys.path.append("../..")
from offline_analysis.helper_functions import attributes_int, attributes_str, colors_int, colors_str, target_int, target_str # lists
from offline_analysis.helper_functions import marker_color_position, marker_attribute_position # integers
from offline_analysis.helper_functions import average_epochs, std_epochs, ERP_aug, ERP_probabilities # functions


# Statuses
IDLE = 0
ACCUMULATING = 1
FITTING = 2
READY = 3


class Inference(Node):
    """
    Load ML-model and predict.
    """
    def __init__(
        self,
        path_to_ml_model=".", # Can we set something default that syncs with ml_training?
        model_name="model.sav",
        session="session0001",
        subject="subject0001",
        model_folder=".",
        ):

        super(Inference, self).__init__()

        self.status = IDLE #None # last known status
        self.path_to_ml_model = path_to_ml_model # Path to ml-model on disk

        self._session = session
        self._subject = subject
        self._model_folder = model_folder
        self._model_name = model_name

        try:
            with open(self.path_to_ml_model,'rb') as file:
                self.ml_model = pickle.load(file)   # Load ml-model
        except:
            pass

    def update(self):

        if self.i_events.ready():
            matches_start = match_events(self.i_events,'set_user_no')
            if matches_start is not None:
                for user_no in matches_start['data']:
                    self._subject="subject"+user_no
                    self.logger.debug("Subject was set to: {}".format(self._subject))

            matches_start = match_events(self.i_events,'start')
            if matches_start is not None:
                for user_no in matches_start['data']:
                    self._subject="subject"+user_no
                    self.logger.debug("Subject was set to: {}".format(self._subject))
        
        # Check for status updates.
        if self.i_status_events.ready():

            df_status = get_data(self.i_status_events, 'status') # Get pd.DataFrame with all events with label 'status'
            
            if df_status is not None:
                new_status = int(df_status['data'][0])
                if (new_status == READY) and (self.status != new_status): # Load new model if status is ready and was not ready before.
                    
                    # Load latest model (file starting with "model_" and then has higest lexicographic order)
                    model_path = self._model_folder + "/" + self._subject + "/" + self._session 
                    all_files = os.listdir(model_path)
                    model_files = [f for f in all_files if f.startswith("model_")]
                    model_files.sort()
                    latest_model = model_files[-1]

                    # Read the contents of the highest file
                    self.logger.debug("Trying to load ML-model: {}".format(os.path.join(model_path, latest_model)))
                    with open(os.path.join(model_path, latest_model), "rb") as file:
                        self.ml_model = pickle.load(file) 
                    self.logger.debug("ML-model loaded.")

                self.status = new_status

        # If status is READY, check for data to do prediction on. 
        if self.status == READY:
            if self.i_rolling.ready():
                data = self.i_rolling.data.values
                data = data.T # transpose data to match scikit learn input
                pred = self.ml_model.predict(np.expand_dims(data, axis=0))
                pred = str(int(pred[0]))
                self.logger.debug("Prediction: {}, type: {}".format(pred,type(pred)))

                # Create event and set output port
                pred_event = make_event("predictions", {"class": pred} ,serialize=True)
                self.o.data = pred_event
                self.o.meta = self.i.meta

    def terminate(self):
        pass


# === Not working/used atm ===
class Transform(Node):
    """
    Load ML-model and predict.
    """
    def __init__(
        self,
        path_to_transformer=".",
        ):

        super(Transform, self).__init__()

        self.status = IDLE
        self.path_to_transformer = path_to_transformer # Path to ml-model on disk
        try:
            with open(self.path_to_transformer,'rb') as file:
                self.transformer = pickle.load(file)   # Load ml-model
        except:
            pass


        # Create lsl-outlet
        # ===== Start LSL streams for pushing outlet =====
        _transform_StreamInfo = StreamInfo(
                                            name="Transform",
                                            type="Markers",
                                            channel_count=2,
                                            nominal_srate=0,
                                            channel_format="string",
                                            source_id="Transform_stream_ml_node")
        channel_names=["label", "data"]
        ch_units={"label":"misc","data":"misc"}
        ch_types={"label":"marker","data":"marker"}

        # Set names on the chanels
        chns = _transform_StreamInfo.desc().append_child("channels")
        for label in channel_names:
            ch = chns.append_child("channel")
            ch.append_child_value("label", label)
            ch.append_child_value("unit", ch_units[label]) # Is this correct value?
            ch.append_child_value("type", ch_types[label]) # Is this correct value?

        # Create outlet
        self._transform_StreamInfo = StreamOutlet(_transform_StreamInfo)
        # self._predictions_StreamOutlet.push_sample(["psd_lr",str(self._out[0])], time())

    def update(self):

        # Check for status updates.
        if self.i_status.ready():

            #new_status = int(get_data(self.i_status, 'status')["data"][0]) # Get pd.DataFrame with all events with label 'status'

            df_status = get_data(self.i_status, 'status') # Get pd.DataFrame with all events with label 'status'
            if df_status is not None:
                new_status = int(df_status['data'][0])
                # TODO: Ska man snarare kolla om i_status innehåller label "ml-model updated" eller liknande.
                if (new_status == READY) and (self.status != new_status): # Load new model if status is ready and was not ready before.
                    with open(self.path_to_ml_model,'rb') as file:
                        self.ml_model = pickle.load(file)   # Load ml-model
                self.status = new_status

        # If inference active, check for data to do prediction on. 
        if self.status == READY:
            if self.i_eeg.ready():
                data = self.i_eeg.data.values
                data = data.T
                #data = data.T #transpose(1,0) # transpose data to match scikit learn input
                pred = self.ml_model.predict(np.expand_dims(data, axis=0))
                self._predictions_StreamOutlet.push_sample(["prediction",str(pred[0].tolist())], time()) # TODO: Ändra label i psychopy så att den lyssnar på denna. Förr "psd_lr" Done/Martin
                self.logger.debug("Prediction: {}".format(pred))


    def terminate(self):
        pass



class AverageERP(Node):
    """
    Average ERPs for each label

    For epochs with different class labels (from the CBM-game), this node is trying to find the odd-one-out class.
        - Epoched data is collected for each class of stimili. 
        - For each class the epochs are then averaged. 
        - Covariance matrices for each average epochs are then computed. 
        - The covariance matrices are then compared and one is picked to be the odd-one-out.
    """

    def __init__(
        self,
        ):

        super(AverageERP, self).__init__()

        self.no_epoch_samples = 640
        self.accumulate_data = False
        self.meta_label = ("epoch", "context")

        # Parameters NOT set by user
        self._status_admin = IDLE
        self._shape = None
        self._X_train = None
        self._y_train = None
        self._cov = Covariances()

    def update(self):

        # == Check and update status (similar to save_numpy.py): ==
        if self._status_admin == False:
            self.accumulate_data = True     
        else: # status_admin == True
            if self.i_status_events.ready():

                # Find status_events with "status" label.
                matches = match_events(self.i_status_events,'status') # 1 is data value for status == ACCUMULATING
                
                # If there is an ACCUMULATING status received
                if matches is not None and int(matches['data'][-1]) == ACCUMULATING: # If there is a status sent
                    if self.accumulate_data == False: # If this is first update where data is accumulating, generate filename and reset params.
                        self._shape = None
                        self._X_train = None
                        self._y_train = None
                    self.accumulate_data = True
                elif matches is not None: # If the status is not ACCUMULATING (if matches is none, no status sent, continue with the latest activity)
                    self.accumulate_data = False


                # TODO: Now we have double information from engine.py. Don't we want to have a category (of actions)
                #       that contains messages that are relevant for what timeflux should do (save/acumulate/delete/data etc.)
                # TODO; check if this works or not! 

                # Check for "actions" (new for engine.py communicaiton)
                matches_start = match_events(self.i_events,'start') # 1 is data value for status == ACCUMULATING
                if matches_start is not None:
                    for user_no in matches_start['data']:
                        self._shape = None
                        self._X_train = None
                        self._y_train = None
                        self.accumulate_data = True


                # TODO: Here, we acctually want to do the same thing for "stop" and "end". Altleast for now. Fix this.

                matches_stop = match_events(self.i_events,'stop') # 1 is data value for status == ACCUMULATING
                if matches_stop is not None:
                    for stop_event in matches_stop['data']:
                        if stop_event == "3000":
                            self.accumulate_data = False

                            # Reset data arrays
                            self._shape = None
                            self._X_train = None
                            self._y_train = None

                matches_end = match_events(self.i_events,'end') # 1 is data value for status == ACCUMULATING
                if matches_end is not None:
                    for end_event in matches_end['data']:
                        if end_event == "9999":
                            self.accumulate_data = False

                            # Reset data arrays
                            self._shape = None
                            self._X_train = None
                            self._y_train = None

        # == Accumulate incoming data (similar to save_numpy.py) ==

        if self.accumulate_data:

            port = self.i_epochs # Port with EEG data. 
            if self.i_epochs.ready():

                index = port.data.index.values # earliest timestamp of recieved epoch # NOT USED ATM?
                data = port.data.values
                data = data.transpose(1,0) # transpose data to match scikit learn input
                label = get_meta(port, self.meta_label) # get label of epoch

                # Funcitonallity for recieving multiple epochs during one update iteration.
                keys = get_dict_keys_by_start(port.meta, "epoch")
                labels = []
                tss = [] # Timestamps
                for key in keys:
                    #label = get_meta(port, self.meta_label) # get label of epoch
                    label = str(get_meta(port, (key,"context"))) # get label of epoch
                    ts = get_meta(port, (key, "onset"))
                    labels.append(label)
                    tss.append(ts)

                if len(keys) != len(labels):
                    die # Variable that does not exist -> crashes the program.

                index = np.reshape(index, (len(keys), self.no_epoch_samples))
                data = np.reshape(data, (len(keys), data.shape[0], self.no_epoch_samples))

                # Check shape of epoch
                if self._shape and (data.shape[1:] != self._shape):
                    self.logger.warning("Invalid shape: {}".format(data.shape[1:]))
                elif self.meta_label is not None and len(labels)!=len(keys):
                    self.logger.warning("Invalid label")

                else:

                    # == Append data/labels to data matrix/label vector ==
                    # TODO: If we are ony interested in the averaged matrices, there is no point in saving the full dataframes like this.

                    # If _X_train is None: create array, else: append to _X_train
                    if self._X_train is None:
                        self._X_train = np.array(data)
                        self._shape = self._X_train.shape[1:]
                        # self._X_train_ts = np.array(index) # skip timestamps for now.

                    else:
                        self._X_train = np.vstack((self._X_train, data))
                        #self._X_train_ts = np.vstack((self._X_train_ts, index)) # skip timestamps for now.

                    # If _y_train is None: create array, else: append to _y_train
                    if label is not None:
                        if self._y_train is None:
                            self._y_train = np.array(labels)
                            #self._y_train_ts = np.array([tss]) # skip timestamps for now.
                        else:
                            self._y_train = np.append(self._y_train, labels)
                            #self._y_train_ts = np.append(self._y_train_ts, [tss]) # skip timestamps for now.

                # ==== Data averageing and analysis =====
    
                if (self._X_train is not None) and (self._y_train is not None):

                    # Check the unique labels

                    labels_unique = pd.unique(self._y_train) # pd.unique() is faster than np.unique() (+ gives unsorted values by default)
                    labels = self._y_train # pd.unique() is faster than np.unique() (+ gives unsorted values by default)
                    self.logger.debug("Shape self._y_train;: {}. labels_unique: {}".format(self._y_train.shape, labels_unique))

                    colors = {key: str(value) for value, key in enumerate(colors_str, start=0)}
                    attributes = {key: str(value) for value, key in enumerate(attributes_str, start=0)}

                    labels_color =  np.empty(labels.shape, dtype=object)
                    labels_attribute =  np.empty(labels.shape, dtype=object)

                    # For each color, ceate a list of indices indicating this color. Then, build a new labels_color vector based on color only.
                    # (Done by checking the 'marker_color_position'-th position in each label to see what is the corresponding color)
                    for key, value in colors.items():
                        indices = [index for index, entry in enumerate(labels) if entry[marker_color_position] == value]
                        labels_color[indices] = key 

                    # Do the same for attributes...
                    for key, value in attributes.items():
                        indices = [index for index,entry in enumerate(labels) if entry[marker_attribute_position] == value]
                        labels_attribute[indices] = key


                    # ==== If we have enough labels: Find indicating indices for each color and attribute ====
                    if len(np.unique(labels_color)) >= 5:

                        # == Average epochs for colors/attributes respectively ==

                        # By color
                        X_avg_color, color_order = average_epochs(self._X_train, labels_color, colors.keys())
                        X_avg = X_avg_color
                        category_order = list(color_order)

                        # By color and attribute
                        """
                        X_avg_attribute, attribute_order = self.average_epochs(self._X_train, labels_attribute, attributes.keys()) 
                        X_avg = np.vstack((X_avg_color, X_avg_attribute))
                        category_order = list(color_order) + list(attribute_order)
                        """
                        self.logger.debug("shape _X_train: {}".format(self._X_train.shape))

         
                        # == Decide how to run the algorithm here ==

                        #X_aug = ERP_aug(X_avg, cov) # Run this is augment covaraince matrices. Obs. not obvious how to do this in the unsupervised setting.
                        #pred = ERP_probabilities(X_avg, self._cov, map2prob='softmax', compare='avg')
                        pred = ERP_probabilities(X_avg, self._cov)
                        self.logger.debug("Predictions: {}".format(pred))

                    else:
                        # As an initial guess we set uniform probability over all classes
                        pred = list(np.array([1.,1.,1.,1.,1])/5.0)


                    # == Send results back to engine ==
                    labels_list = list(colors.keys()) + list(attributes.keys())
                    pred_dict = dict(zip(labels_list, pred))

                    # Create event and set output port
                    pred_event = make_event("predictions", pred_dict ,serialize=True)
                    self.o.data = pred_event
                    self.o.meta = self.i.meta

    def terminate(self):
        pass