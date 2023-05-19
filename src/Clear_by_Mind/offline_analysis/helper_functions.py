"""
Helper functions used for analysis of eeg epochs. 
The intention is that these should be used both in offline analysis and Timeflux when running things in real-time.
"""
import numpy as np
import pandas as pd
import pyriemann
from pyriemann.utils.distance import distance_riemann, distance
from pyriemann.estimation import Covariances
from scipy.special import softmax


# ==== Data structures/maps ====

# Lists of which target classes are colors and attributes respectively  
attributes_int = [0,1,2,3]
attributes_str = ["hat", "tie", "briefcase", "skirt"]  
colors_int = [4,5,6,7,8]
colors_str = ["yellow", "blue", "green", "red", "child"]
target_int = attributes_int + colors_int
target_str = attributes_str + colors_str

# Map on how colors and attrubutes are encoded in the marker-string
color_str2nbr_dict = dict(zip(colors_str, list(range(0,len(colors_str))))) # {"yellow": 0, "blue": 1, "green": 2, "red": 3, "child": 4}
attribute_str2nbr_dict = dict(zip(attributes_str, list(range(0,len(colors_str))))) # {"hat": 0, "tie": 1, "briefcase": 2, "skirt": 3}

# Maps from [nbr labels --> attribute/color labels] and [attribute/color labels --> nbr labels] 
target_nbr2str_dict = dict(zip(target_int, target_str)) # {0: "hat", 1: "tie", 2: "briefcase", 3: "skirt", 4: "yellow", 5: "blue", 6: "green", 7: "red", 8: "child"}
target_str2nbr_dict = dict(zip(target_str, target_int)) # {"hat": 0, "tie": 1, "briefcase": 2, "skirt": 3, "yellow": 4, "blue": 5, "green": 6, "red": 7, "child": 8}

# The position in the "10XX" string that represents color and attribute respectively.
marker_color_position = 3
marker_attribute_position = 2


def average_epochs(X, y, unique_labels=None):
    """
    Function for averaging epochs for each unique label in the dataset (X,y)

    :param X: epoch data (epochs x channels x samples)
    :param y: labels
    :param unique_labels: Unique labels to find averages for. Use this if we want a specific order of the outputed epochs. 
    :return X_avg, unique_labels: averaged epochs for each class (in order of labels apparance), corresponding labels
    """ 
    if unique_labels is None:
        unique_labels = pd.unique(y)

    X_avg = None
    for label in unique_labels:
        index = np.where(y==label)[0] # index for all epochs with y=label. Use '[0]' to unpack tuple
        temp = np.mean(X[index,:,:], axis=0)  # shape is: (n_epochs, n_channels, n_ts)
        temp = np.expand_dims(temp, axis=0)
        if X_avg is None:
            X_avg = temp
        else:
            X_avg = np.vstack((X_avg, temp))
    return X_avg, unique_labels

def std_epochs(X, y, unique_labels=None):
    """
    Function for find standard deviation across epochs for each unique label in the dataset (X,y)

    :param X: epoch data (epochs x channels x samples)
    :param y: labels
    :param unique_labels: Unique labels to find std.dev. for. Use this if we want a specific order of the outputed epochs. 
    :return X_std, unique_labels: standard deviation of epochs of each class (in order of labels apparance), corresponding labels
    """ 
    if unique_labels is None:
        unique_labels = pd.unique(y)

    X_std = None
    for label in unique_labels:
        index = np.where(y==label)[0] # index for all epochs with y=label. Use '[0]' to unpack tuple
        temp = np.std(X[index,:,:], axis=0)  # shape is: (n_epochs, n_channels, n_ts)
        temp = np.expand_dims(temp, axis=0)
        if X_std is None:
            X_std = temp
        else:
            X_std = np.vstack((X_std, temp))
    return X_std, unique_labels

def ERP_aug(X_avg_class):
    """
    Function to augment EEG-epochs

    :param X_avg_class: averaged EEG-epoch for each class of interest (n_classes x n_channels x n_samples)
    :return X_avg_class_aug: augmented EEG-epoch for each class of interest (n_classes x 2*n_channels x n_samples)
    """ 

    X_avg_class_aug = None 
    for i in range(X_avg_class.shape[0]):
 
        X_avg_class_not_i = np.mean(np.delete(X_avg_class, i, axis=0), axis=0) #, keepdims=True)  # shape: (Ch, Ts)
        
        X_aug = np.block([[X_avg_class[i,:,:]],[X_avg_class_not_i]]) # shape: [(Ch, Ts); (Ch, Ts)] --> (2*Ch, Ts)
        X_aug = np.expand_dims(X_aug, axis=0)

        # Verify shapes are ok: # remove
        #print("X_avg_class_i: ", X_avg_class[i,:,:].shape)
        #print("X_avg_class_not_i: ", X_avg_class_not_i.shape)
        #print("X_aug: ", X_aug.shape)

        if X_avg_class_aug is None:
            X_avg_class_aug = X_aug
        else:
            X_avg_class_aug = np.vstack((X_avg_class_aug, X_aug))

    #print("X_avg_class_aug: ", X_avg_class_aug.shape) # remove
    return X_avg_class_aug


def ERP_probabilities(X_avg_class, cov, map2prob="softmax", compare="avg"):
    """
    Function to compute odd-one-out probabilites for a set of EEG-epochs averages for a differnt conditions

    :param X_avg_class: averaged EEG-epoch for each class of interest (n_classes x n_channels x n_samples)
    :param cov: covariance estimator to be used
    :return probabilities: probability for each class the be the odd one out.
    """ 

    dist_vec = np.zeros((X_avg_class.shape[0]))
    dist_mat = np.zeros((X_avg_class.shape[0]-1, X_avg_class.shape[0]))
    # print("X_avg_class.shape: ", X_avg_class.shape) # remove

    
    for i in range(X_avg_class.shape[0]):

        Cov_i = cov.transform(X_avg_class[[i],:,:]) # Covariance matrix for X_avg_class[i], shape: (1,ch,ts)

        # Original method: 
        #  - Take distance between dist(cov(X_avg_class[i]),cov(mean(X_avg_class[~i]))
        if compare == "avg":
            X_avg_class_not_i_avg = np.mean(np.delete(X_avg_class, i, axis=0), axis=0, keepdims=True)  # shape: (1,Ch,Ts)
            Cov_avg_not_i_avg = cov.transform(X_avg_class_not_i_avg)
            dist_vec[i] = distance_riemann(Cov_i[0,:,:], Cov_avg_not_i_avg[0,:,:])

        # Alternative method: 
        #  - Take distance between dist(cov(X_avg_class[i]),cov(X_avg_class[~i]), for EACH X_avg_class[~i]
        #  - OBS. This does not seem to perform as good as the "avg" method.        
        if compare == "individual":
            X_avg_class_not_i = np.delete(X_avg_class, i, axis=0)  # shape: (nof_classes-1,Ch,Ts)
            Cov_avg_not_i = cov.transform(X_avg_class_not_i)
            dist_mat[:,[i]] = distance(Cov_avg_not_i[:,:,:], Cov_i[0,:,:], metric='riemann') # use pyriemann.distance to allow fo a set of SPD matrices in the 2nd argument.
            dist_vec = np.mean(dist_mat, axis=0)

    if map2prob == "softmax":
        return softmax(dist_vec)
    elif map2prob == 'manhattan':
        return dist_vec/sum(dist_vec)
    else:
        return dist_vec
        
    