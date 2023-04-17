from typing import Iterable
from . import constants


def prepare_graph(G):
    """
    A set of operations needed to make the street graph created by osmnx ready for snman operations

    Parameters
    ----------
    G : nx.MultiDiGraph
        street graph

    Returns
    -------
    None
    """

    # ensure consistent data types
    for id, edge in G.edges.items():

        maxspeed = edge.get('maxspeed', '')
        edge['maxspeed'] = int(maxspeed) if maxspeed.isdigit() else -1

        layer = edge.get('layer', '')
        edge['layer'] = int(layer) if layer.isdigit() else 0


def flatten_list(items):
    """
    A simple function for flattening nested lists, from this post:
    https://stackoverflow.com/questions/952914/how-do-i-make-a-flat-list-out-of-a-list-of-lists/40857703?r=Saves_UserSavesList#40857703

    Parameters
    ----------
    items : list
        nested list

    Returns
    -------
    list
        flattened list
    """
    for x in items:
        if isinstance(x, Iterable) and not isinstance(x, (str, bytes)):
            for sub_x in flatten_list(x):
                yield sub_x
        else:
            yield x

            
def order_condition(element):
    """
    Function that reads the order dict from constants and returns the value to the according key in the dict
    
    Parameters
    ----------
    element : string
        lanetype + direction
        
    Returns
    -------
    int
        key for sorting inside a list of lanes"""
    
    order = constants.ORDER_NEW_EDGES
    if element in order.keys():
        return order[element]
    else:
        return 0

def reorder_lanes(ln_list):
    """sorts the ln_list according to the function order_condition
    """
    ln_list.sort(key=order_condition)
    return ln_list
    