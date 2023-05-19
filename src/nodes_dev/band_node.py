"""This module has nodes for importing a classifier with Timeflux."""

import sys
import datetime
import json

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.pipeline import make_pipeline
from mne.decoding import PSDEstimator

from timeflux.core.node import Node
from timeflux.helpers.port import make_event


class ChannelVarianceNode(Node):

    def __init__(self, device="museS", output_style="by_channel"):
        # Create pipleine of mne.PSDEstimator and self-created BandCalculator (calculates band average)
        self.model = make_pipeline(ChannelVariance(), verbose=False)
        self.device = device
        self.output_style = output_style

        # TODO: The museS have the elctrode names as column names already. Perhaps we can change this for the crown earlier in the pipeline! #remove
        if self.device == "crown":
              self.channel_labels = ["CP3", "C3", "F5", "PO3", "PO4", "F6", "C4", "CP4"]

        if self.device == "museS":
              self.channel_labels = ['TP9', 'AF7', 'AF8', 'TP10']


    def update(self):

        if self.i.ready():

            now = datetime.datetime.now()
            data = self.i.data.values # Get data as np array

            meta = list(self.i.data.columns) # Try to get channel names. Ex. for muse: ['TP9', 'AF7', 'AF8', 'TP10']
            data = data.T[np.newaxis,:,:] # reshape to (n_epochs,n_channels,n_times)

            trans = self.model.transform(data) # Use pipeline/model to calculate bands

            if self.device == "museS":

                self.i.meta['start_time'] = self.i.data.index[0]
                self.i.meta['stop_time'] = self.i.data.index[-1]

                # Send prediction to output port.
                trans_dict = dict(zip(self.channel_labels, trans[0,:].tolist()))
                pred_event = make_event("variance", trans_dict ,serialize=True)
                self.o.data = pred_event
                self.o.meta = self.i.meta

            elif self.device == "crown":
        
                self.i.meta['start_time'] = self.i.data.index[0]
                self.i.meta['stop_time'] = self.i.data.index[-1]

                # Send prediction to output port.
                trans_dict = dict(zip(self.channel_labels, trans[0,:].tolist()))
                pred_event = make_event("variance", trans_dict ,serialize=True)
                self.o.data = pred_event
                self.o.meta = self.i.meta

        else:
            # If there is no data, do nothing. 
            pass


class ChannelVariance(BaseEstimator, TransformerMixin):
    '''
    Class for calculating channel variance. Expects epoched data as input.

    Parameters:
        -

    Returns:
        Average power for the specified bands in the order of the parameter 'bands'.
    '''
    def __init__(self, data_shape=None, channel_names=None): # no *args or **kargs
        self.data_shape = data_shape
        self.channel_names = channel_names

    def fit(self, X, y=None):
        return self # nothing else to do

    def transform(self, X):

        if self.data_shape is not None:
            # Check for changeing dimensios...
            if self.data_shape != X.shape:
                print("dimensions have changed")
        else:
            out = np.empty((1, X.shape[1]))
            return np.var(X, axis=2) # Swapped from np.std() to np.var()