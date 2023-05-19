from timeflux.helpers.port import match_events

def match_keys(port, key):
    """Find the given key in an event DataFrame

    Args:
        port (Port): The event port.
        key (str): The key string to look for in the data column.

    Returns:
        DataFrame: The df of matched events, or `None` if there is no match.

    """
    matches = None
    if port.ready():
        key_matches = port.data[port.data["label"] == "KeyPress"]
        matches = key_matches[key_matches["data"] == key]
        if matches.empty:
            matches = None
    return matches


def match_label_and_data(port, label,data):
    """Find the given combination of label and data in an event DataFrame

    Args:
        port (Port): The event port.
        label (str): The label string to look for in the label column.
        data (str): The data string to look for in the data column.

    Returns:
        DataFrame: The df of matched events, or `None` if there is no match.

    """
    matches = None
    if port.ready():
        key_matches = port.data[port.data["label"] == label]
        matches = key_matches[key_matches["data"] == data]
        if matches.empty:
            matches = None
    return matches


def match_keys_and_events(port, label, key):
    """Find if either lable or key is in the DataFrame

    Args:
        port (Port): The event port.
        label (str): The label string to look for in the label column.
        key (str): The key string to look for in the data column.

    Returns:
        DataFrame: The df of matched events, or `None` if there is no match.

    """
    matches = None
    matches_key = match_keys(port,key)
    matches_events = match_events(port,label)
    if matches_key is not None and matches_events is not None:
        matches = matches_key.append(matches_events)
    elif matches_key is not None:
        matches = matches_key
    elif matches_events is not None:
        matches = matches_events

    return matches

def get_data(port, label):
    """Get all data from the port with the given label

    Args:
        port (Port): The event port.
        label (str): The string to look for in the label column.

    Returns:
        DataFrame: The data, or `None` if there is no match.

    """
    matches = None
    if port.ready():
        matches = port.data[port.data["label"] == label]
        if matches.empty:
            matches = None
    return matches

def get_dict_keys_by_start(dict, key_start, default=None):

    keys = dict.keys()
    len_key_start = len(key_start)
    return_list = []


    if keys is None:
        return default
    for key in keys:
        if key[0:len(key_start)] == key_start:
            return_list.append(key)
    return return_list



    