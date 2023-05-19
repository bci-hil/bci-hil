import os
import importlib
import json
import glob
from jsonschema import validate
from datetime import datetime
from pathlib import Path
from time import time
import pickle

import numpy as np
import pandas as pd
from sklearn.pipeline import make_pipeline

from timeflux.core.node import Node
from timeflux.core.exceptions import ValidationError
from timeflux.helpers.background import Task
from timeflux.helpers.port import make_event, match_events
from timeflux.helpers.clock import now

# status_fitting
FITTING_IDLE = 0
FITTING_ONGOING = 1
FITTING_READY = 2
FITTING_ERROR = 3

# System status
IDLE = 0
ACCUMULATING = 1
FITTING = 2
READY = 3


class TrainingML(Node):
    """

    """

    def __init__(
        self,
        steps = None,
        load_pipeline_from_file = False,
        session="session0001",
        subject="subject0001",
        data_folder=".",
        path_save_model=".",
        ):

        # ==== Set parameters ====

        # Parameters set by user
        self.load_pipeline_from_file = load_pipeline_from_file # file

        self._session = session
        self._subject = subject
        self._data_folder = data_folder

        self._path_save_model = path_save_model

        # Internal parameters
        self._status = IDLE
        self._status_fitting = FITTING_IDLE

        # ==== Intialization ====
        self._make_pipeline(steps) # Build pipeline to be trained

    def update(self):

        # Remove
        #self.logger.debug("ml_traning status: {}".format(self._status))
        #self.logger.debug("ml_traning status_fittning: {}".format(self._status_fitting))


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
            df = self.i_status_events.data # df is a pandas dataframe with our reglar structure.

            if not df[df['label']=='status'].empty: # make sure we have atleast one status message in the df.
                new_status = df[df['label']=='status']['data'].iloc[-1]  # df[df['label']=='status']) gives rows where label = 'status'
                self._status = int(new_status) # Convert 'str' data to 'int')
                self.logger.debug("Status received: {}".format(self._status))



        # ===================================================================
        # ==== Start/stop fitting and update _status_fitting accordingly ====
        # ===================================================================

        # ==== Start fitting ====
        if self._status == FITTING and self._status_fitting == FITTING_IDLE:

            # Set status_fitting = FITTING_ONGOING and push status_fitting and send output port
            self._status_fitting = FITTING_ONGOING
            self.logger.debug("Fitting-status set to: {}, at time: {}".format(self._status_fitting, now()))

            # Create event and set output port
            status_event = make_event("status_fitting", self._status_fitting, serialize=True)
            self.o.data = status_event
            self.o.meta = self.i.meta


            # =====================================================
            # ==== Load data to use for fitting the pipeline: =====
            # =====================================================

            # One way of doing transfer-learning can be done by choosing training data in a selective way. Such functionality would go here.
            # Currently only data from the current subject and session is loaded.

            X_training_data = None #None #np.empty((0,self._X_train.shape[1],self._X_train.shape[2])) # Placeholder for data
            y_training_data = np.empty((0)) # Placeholder for data

            folder = '{}/{}/{}'.format(self._data_folder, self._subject, self._session)
            self.logger.debug("Trying to loading data for fitting from folder: {}, status: {}, status fitting: {}".format(folder, self._status, self._status_fitting))

            for filename_x in glob.glob('{}/X_*'.format(folder)): # Go through all files with X-data
                self.logger.debug("Loading X-data from file: {}".format(filename_x))
                with open(filename_x,'rb') as file:
                    X = pickle.load(file)   # Load file
                    if X is not None:
                        if X_training_data is None:
                            X_training_data = np.empty((0, X.shape[1], X.shape[2]))   
                        X_training_data = np.concatenate((X_training_data,X),axis=0) # Concatenate new data with previous data.
                for filename_y in glob.glob('{}/y_*{}'.format(folder,filename_x[-23:])): # Go through all y-data. Use the date and time from the x-file to open matching y-file.
                    self.logger.debug("Loading y-data from file: {}".format(filename_y))
                    with open(filename_y,'rb') as file:
                        y = pickle.load(file)    # Load file
                        if y is not None:
                            y_training_data = np.concatenate((y_training_data,y),axis=0) # Concatenate new data with previous data.

            # Set combined data to training data.
            self._X_train = X_training_data 
            self._y_train = y_training_data

            self.logger.debug("Data for fitting loaded done. _y_train.shape: {} ".format(self._y_train.shape))
            try:
                self.logger.debug("Data for fitting loaded done. _X_train.shape: {}".format(self._X_train.shape))
            except:
                self.logger.debug("Data for fitting loaded done. _X_train: {}".format(self._X_train))


            # =========================================
            # ==== Transfer learning would go here ====
            # =========================================

            # Transfer learning can also be achieved by transforming data or using weight form previously trained models. Such functionality would go here.

            # =====================
            # ==== Train model ====
            # =====================

            self.logger.debug("Starting fitting: _status: {}, _status_fitting: {}".format(self._status, self._status_fitting))

            self._task = Task(
                self._pipeline, "fit", self._X_train, self._y_train
            ).start() # Start subprocess that trains the model.

            self.logger.debug("FITTING ONGOING.")


        # ==== If fitting is ongoing, check if it's done. If so, update fitting_status and save model ====
        if self._status_fitting == FITTING_ONGOING:

            # status is a dict with {'instance': Pipleine(...), 'sucess': boolean, 'time': fitting-time(?)}, or None (if we are still fitting).
            status = self._task.status() # None if there was no data

            if status: 
                if status["success"]:

                    self._pipeline = status["instance"]

                    # Set status_fitting = FITTING_ONGOING and push status_fitting and send output port
                    self._status_fitting = FITTING_READY
                    self.logger.debug("FITTING READY. Fitting-status: {}, fitting duration: (status[\"time\"]): {}".format(self._status_fitting, status["time"]))  
                    self.logger.debug("Fitted pipeline: {}".format(status["instance"]))

                    # Create event and set output port
                    status_event = make_event("status_fitting", self._status_fitting, serialize=True)
                    self.o.data = status_event
                    self.o.meta = self.i.meta

                    # ==== Save pipeline ====
                    #if self._save_data:
                    folder = '{}/{}/{}'.format(self._path_save_model, self._subject, self._session)
                    self._time_lastest_fitting = datetime.now().strftime("%Y-%m-%d-%H:%M:%S")
                    filename_pickle = '{}/model_{}.sav'.format(folder, self._time_lastest_fitting)
                    pickle.dump(self._pipeline, open(filename_pickle, 'wb'))


                else:
                    self.logger.debug("FITTING FAILED. _task().status()[\"success\"]: {}".format(status["success"]))
                    self._status_fitting = FITTING_ERROR

            # If self._task.status() is none
            else: 
                pass
                self.logger.debug("self._task.status(): {}".format(self._task.status()))


        # ==== Status-admin has received knows that fitting is ready and has switched status ====        
        if self._status != FITTING and self._status_fitting == FITTING_READY:

            self._status_fitting = FITTING_IDLE
            self.logger.debug("Fitting-status: {}, at time (now): {}".format(self._status_fitting, now()))     
            self.logger.debug("Fitting cycle completed. _status: {}, _status_fitting: {}".format(self._status, self._status_fitting)) # remove?
            
            # Create event and set output port
            status_event = make_event("status_fitting", self._status_fitting, serialize=True)
            self.o.data = status_event
            self.o.meta = self.i.meta

        # ==== We have had a fitting error. Send status and go back to FITTING_IDLE ====
        if self._status_fitting == FITTING_ERROR:
            self.logger.debug("Fitting-status: {}, at time (now): {}".format(self._status_fitting, now()))     

            # Create event and set output port
            status_event = make_event("status_fitting", self._status_fitting, serialize=True)
            self.o.data = status_event
            self.o.meta = self.i.meta

            self._status_fitting = FITTING_IDLE

        # ==== Fitting has for some reason been aborted - abort the fitting ====
        if self._status != FITTING and self._status_fitting == FITTING_ONGOING:
            # Kill the fit subprocess
            if self._task is not None:
                self._task.stop()

            self._status_fitting = FITTING_IDLE
            self.logger.debug("Fitting-status: {}, at time (now): {}".format(self._status_fitting, now()))     
            
            # Create event and set output port
            status_event = make_event("status_fitting", self._status_fitting, serialize=True)
            self.o.data = status_event
            self.o.meta = self.i.meta

    def terminate(self):

        # Kill the fit subprocess
        if self._task is not None:
            self._task.stop()

    def _make_pipeline(self, steps):

        # Load pipeline from file
        if self.load_pipeline_from_file:
            self._pipeline = pickle.load(open(self.load_pipeline_from_file, 'rb'))

        # Create pipline from specification in .yaml file
        else:
            schema = {
                "type": "array",
                "minItems": 1,
                "items": {
                    "type": "object",
                    "properties": {
                        "module": {"type": "string"},
                        "class": {"type": "string"},
                        "args": {"type": "object"},
                    },
                    "required": ["module", "class"],
                },
            }
            try:
                validate(instance=steps, schema=schema)
            except Exception as error:
                raise ValidationError("steps", error.message)
            pipeline = []
            for step in steps:
                try:
                    args = step["args"] if "args" in step else {}
                    m = importlib.import_module(step["module"])
                    c = getattr(m, step["class"])
                    i = c(**args)
                    pipeline.append(i)
                except ImportError as error:
                    raise ValidationError("steps", f"could not import '{step['module']}'")
                except AttributeError as error:
                    raise ValidationError(
                        "steps", f"could not find class '{step['class']}'"
                    )
                except TypeError as error:
                    raise ValidationError(
                        "steps",
                        f"could not instantiate class '{step['class']}' with the given params",
                    )
            # TODO: memory and verbose args
            self._pipeline = make_pipeline(*pipeline, memory=None, verbose=False)
