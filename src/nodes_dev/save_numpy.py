"""Save data as Numoy array"""

import os
from datetime import datetime, timedelta
import pickle

import numpy as np
import pandas as pd

from timeflux.core.node import Node
from timeflux.helpers.port import get_meta, match_events
from timeflux.nodes_dev.helpers import get_dict_keys_by_start

# Statuses
IDLE = 0
ACCUMULATING = 1
FITTING = 2
READY = 3

class SaveNumpy(Node):
    """Save to nympy arrays

        Explaination goes here

    Attributes:
        i (Port): Default data input, expects DataFrame.
        i_events (Port): Event input, expects DataFrame.
        o (Port): Default output, provides DataFrame and meta.
        o_* (Port): Dynamic outputs, provide DataFrame and meta.
        ...

    Args:
        save_data (bool): ...
        session (str): ...
        subject (str): ...
        data_folder (str): ...
        ...

    Example:
        ...

    """

    def __init__(
        self,
        save_data=True,
        session="session0001",
        subject="subject0001",
        data_folder=".",
        status_admin = False,
        save_interval = 3, # How long before writing new data to file (in seconds)
        no_epoch_samples=256 # How many samples each epoch is expected to contain.
    ):

        # Parameters set by user
        self._save_data = save_data
        self._session = session
        self._subject = subject
        self._data_folder = data_folder
        self._status_admin = status_admin # Flag if status admin is used in system. 
        self._folder = '{}/{}/{}'.format(self._data_folder, self._subject, self._session)
        self.save_interval = save_interval
        self.no_epoch_samples = no_epoch_samples
        

        # Parameters NOT set by user
        self._save_time_next = datetime.now() + timedelta(0, self.save_interval)
        self.accumulate_data = False
        self.save_data_continuously = False
        self._shape = None
        self._X_train = None
        self._y_train = None
        self.meta_label = ("epoch", "context")

        self._X_train_ts = None
        self._y_train_ts = None

        self.file_name = None

    def update(self):

        if self._status_admin == False:
            self.accumulate_data = True
            self.save_data_continuously = False

        else: # status_admin == True

            if self.i_status_events.ready():

                # Find status_events with "status" label.
                matches = match_events(self.i_status_events,'status') # 1 is data value for status == ACCUMULATING

                # If there is an ACCUMULATING status received
                if matches is not None and int(matches['data'][-1]) == ACCUMULATING: 
                    if self.accumulate_data == False: # If this is first update where data is accumulating, generate filename and reset params.
                        self.file_name = datetime.now().strftime("%Y-%m-%d-%H:%M:%S")
                        self._shape = None
                        self._X_train = None
                        self._y_train = None
                    self.accumulate_data = True
                    self.save_data_continuously = True

                # If the received status was not ACCUMULATING
                elif matches is not None: 
                    self.accumulate_data = False
                    self.save_data_continuously = False

            if self.i_events.ready():

                matches_start = match_events(self.i_events,'set_user_no')
                if matches_start is not None:
                    for user_no in matches_start['data']:
                        self._subject="subject"+user_no
                        self.logger.debug("Subject was set to: {}".format(self._subject))
                        self._folder = '{}/{}/{}'.format(self._data_folder, self._subject, self._session)


                # Check for "actions" (new for engine.py communicaiton)
                matches_start = match_events(self.i_events,'start') # 1 is data value for status == ACCUMULATING
                if matches_start is not None:
                    for user_no in matches_start['data']:
                        self.file_name = datetime.now().strftime("%Y-%m-%d-%H:%M:%S")
                        self._shape = None
                        self._X_train = None
                        self._y_train = None
                        self._subject="subject"+user_no
                        self.logger.debug("Subject was set to: {}".format(self._subject))
                        self._folder = '{}/{}/{}'.format(self._data_folder, self._subject, self._session)

                        # Also save timestamps:
                        self._y_train_ts = None
                        self._X_train_ts = None

                        self.accumulate_data = True
                        self.save_data_continuously = True

                # TODO: Now we stop saving data immediately. We should wait a little s.t. the current epochs have time to be saved.

                # Stop session. Everything went fine.
                matches_stop = match_events(self.i_events,'stop')
                if matches_stop is not None:
                    for stop_event in matches_stop['data']:
                         # Check that the stop_event was "3000".
                        if stop_event == "3000":
                            self.accumulate_data = False
                            self.save_data_continuously = False

                            # Reset data arrays
                            self._shape = None
                            self._X_train = None
                            self._y_train = None

                            # Also reset timestamps:
                            self._y_train_ts = None
                            self._X_train_ts = None

                # Used in CBM when a session ends and the true labels is sent after the session/run
                matches_end = match_events(self.i_events,'end')
                if matches_end is not None:
                    for end_event in matches_end['data']:
                        target = int(end_event[2:4]) # get the 2 last numbers 
                        filename_pickle = '{}/t_{}.sav'.format(self._folder, self.file_name)
                        pickle.dump(target, open(filename_pickle, 'wb'))

                # Cances session, something went wrong. Delete data
                matches_cancel = match_events(self.i_events,'cancel')
                if matches_cancel is not None:
                    for cancel_event in matches_cancel['data']:
                        if cancel_event == "9999":
                            self.accumulate_data = False
                            self.save_data_continuously = False

                            # Reset data arrays
                            self._shape = None
                            self._X_train = None
                            self._y_train = None

                            # Also reset timestamps:
                            self._y_train_ts = None
                            self._X_train_ts = None

                            # Remove files from trail.
                            self.remove_pickled_data()
                """
                # End session. Someting went wrong. Try to delete the data.
                matches_end = match_events(self.i_events,'end')
                if matches_end is not None:
                    for end_event in matches_end['data']:
                        if end_event == "9999":
                            self.accumulate_data = False
                            self.save_data_continuously = False

                            # Reset data arrays
                            self._shape = None
                            self._X_train = None
                            self._y_train = None

                            # Also reset timestamps:
                            self._y_train_ts = None
                            self._X_train_ts = None

                            # Remove files from trail.
                            self.remove_pickled_data()
                        
                        else:
                            target = int(end_event[2:4]) # get the 2 last numbers 
                            filename_pickle = '{}/t_{}.sav'.format(self._folder, self.file_name)
                            pickle.dump(target, open(filename_pickle, 'wb'))
                                # End session. Someting went wrong. Try to delete the data.

                matches_cancel = match_events(self.i_events,'cancel')
                if matches_cancel is not None:
                    for cancel_event in matches_cancel['data']:
                        if cancel_event == "9999":
                            self.accumulate_data = False
                            self.save_data_continuously = False

                            # Reset data arrays
                            self._shape = None
                            self._X_train = None
                            self._y_train = None

                            # Also reset timestamps:
                            self._y_train_ts = None
                            self._X_train_ts = None

                            # Remove files from trail.
                            self.remove_pickled_data()
                """

        # Accumulate incoming data
        if self.accumulate_data:

            port = self.i_epochs # Port with epoched EEG data. 
            if self.i_epochs.ready():

                index = port.data.index.values # Timestamp of receieved epoch 
                data = port.data.values
                data = data.transpose(1,0) # transpose data to match scikit learn input

                # Functionality for recieving multiple epochs during one update iteration.
                keys = get_dict_keys_by_start(port.meta, "epoch")
                labels = []
                tss = [] # Timestamps
                for key in keys:
                    #label = get_meta(port, self.meta_label) # get label of epoch # remove
                    label = get_meta(port, (key,"context")) # get label of epoch
                    ts = get_meta(port, (key, "onset"))
                    labels.append(label)
                    tss.append(ts)
                
                if len(keys) != len(labels):
                    die # Make the program stop

                index = np.reshape(index, (len(keys), self.no_epoch_samples))
                data = np.reshape(data, (len(keys), data.shape[0], self.no_epoch_samples))

                # Check shape of epoch
                if self._shape and (data.shape[1:] != self._shape):
                    self.logger.warning("Invalid shape: {}".format(data.shape[1:]))
                elif self.meta_label is not None and len(labels)!=len(keys):
                    self.logger.warning("Invalid label")

                # Somtimes we get the twice the amount of samples in our epochs. In the meanwhile do simple fix with else...
                # TODO: Fix this. (also in ml_inference.py)

                else:

                    # If _X_train is None: create array, else: append to _X_train
                    if self._X_train is None:
                        self._X_train = np.array(data)
                        self._X_train_ts = np.array(index)
                        self._shape = self._X_train.shape[1:]
                    else:
                        self._X_train = np.vstack((self._X_train, data))
                        self._X_train_ts = np.vstack((self._X_train_ts, index))
                        
                    # If _y_train is None: create array, else: append to _y_train
                    if label is not None:
                        if self._y_train is None:
                            self._y_train = np.array([labels])
                            self._y_train_ts = np.array([tss])
                        else:
                            self._y_train = np.append(self._y_train, [labels])
                            self._y_train_ts = np.append(self._y_train_ts, [tss])

        # Continuously save data to specified file (instead of just writing once upon termination)
        if self.save_data_continuously and datetime.now() >= self._save_time_next:
            self.save_epochs_to_file()
            self._save_time_next =  datetime.now() + timedelta(0,self.save_interval)

    def save_epochs_to_file(self):


        self.logger.debug("Trying to save data to: {}/Xts_{}.sav".format(self._folder, self.file_name))

        if self._X_train is not None:
            
            # Check if folder exists. If not, create it.
            if not (os.path.exists(self._folder) and os.path.isdir(self._folder)):
                try:
                    self.logger.debug("Trying to create folder: {}".format(self._folder))        
                    os.makedirs(self._folder)
                except OSError as e:
                    pass    
            
            # Save data and labels.
            filename_pickle = '{}/X_{}.sav'.format(self._folder, self.file_name)
            pickle.dump(self._X_train, open(filename_pickle, 'wb'))
            filename_pickle = '{}/y_{}.sav'.format(self._folder, self.file_name)
            pickle.dump(self._y_train, open(filename_pickle, 'wb'))

            # Also save the timestamps.
            filename_pickle = '{}/Xts_{}.sav'.format(self._folder, self.file_name)
            pickle.dump(self._X_train_ts, open(filename_pickle, 'wb'))
            filename_pickle = '{}/yts_{}.sav'.format(self._folder, self.file_name)
            pickle.dump(self._y_train_ts, open(filename_pickle, 'wb'))
            
            self.logger.debug("Data saved.")

        else:
            self.logger.debug("No data is available (yet).")
   


    def remove_pickled_data(self):
        self.logger.debug("Trying to remove [data, label, timestamp]-files: {}/*_{}".format(self._folder, self.file_name))        

        # Remove files from trail.
        try:
            filename_pickle = '{}/X_{}.sav'.format(self._folder, self.file_name)
            os.remove(filename_pickle)
            filename_pickle = '{}/y_{}.sav'.format(self._folder, self.file_name)
            os.remove(filename_pickle)

            # Also remove timestamps
            filename_pickle = '{}/Xts_{}.sav'.format(self._folder, self.file_name)
            os.remove(filename_pickle)
            filename_pickle = '{}/yts_{}.sav'.format(self._folder, self.file_name)
            os.remove(filename_pickle)

            self.logger.debug("Removal of files ok: {}/*_{}".format(self._folder, self.file_name))        

        except:
            self.logger.debug("Tried to remove [data, label, timestamp]-files, but folder/files didn't exist.")        
        try:
            filename_pickle = '{}/t_{}.sav'.format(self._folder, self.file_name)
            os.remove(filename_pickle)
        except:
            self.logger.debug("Tried to remove target-file, but file did not exist (ok for MI).")   
    


    # Save the data upon termination of the application.
    def terminate(self):
        # Pickle training data
        if self._save_data and self._X_train is not None:
            self.save_epochs_to_file()