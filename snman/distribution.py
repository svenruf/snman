import math
import networkx as nx
from . import constants, lanes, hierarchy


def set_given_lanes(street_graph):
    """
    Sets which lanes are given due to external policy definitions
    e.g. dedicated lanes for public transport, bidirectional lanes for cars, etc.
    """

    #TODO: Add support for dedicated transit lanes

    for id, data in street_graph.edges.items():
        data['given_lanes'] = []

        if data.get('pt_tram') or data.get('pt_bus'):
            data['given_lanes'] += [
                lanes.LANETYPE_MOTORIZED + lanes.DIRECTION_BACKWARD,
                lanes.LANETYPE_MOTORIZED + lanes.DIRECTION_FORWARD
            ]

        else:

            if data.get('hierarchy') in [hierarchy.MAIN_ROAD, hierarchy.LOCAL_ROAD]:
                data['given_lanes'] += [lanes.LANETYPE_MOTORIZED + lanes.DIRECTION_TBD]

            elif data.get('hierarchy') == hierarchy.DEAD_END:
                data['given_lanes'] += [lanes.LANETYPE_MOTORIZED + lanes.DIRECTION_BOTH]

            # In case of highways keep all lanes as they are
            if data.get('hierarchy') == hierarchy.HIGHWAY:
                data['given_lanes'] = data.get(lanes.LANES_DESCRIPTION_KEY)

def create_given_lanes_graph(street_graph):
    """
    Returns a directed graph of given (mandatory) lanes. Lanes with changeable direction are marked with an attribute
    """
    given_lanes_graph = nx.DiGraph()
    given_lanes_graph.graph['crs'] = street_graph.graph['crs']
    given_lanes_graph.add_nodes_from(street_graph.nodes.items())

    for id, data in street_graph.edges.items():
        u = id[0]
        v = id[1]
        given_lanes = data.get('given_lanes',[])

        for lane in given_lanes:
            lane_properties = lanes._lane_properties(lane)

            if lane_properties.direction in [lanes.DIRECTION_FORWARD, lanes.DIRECTION_BOTH]:
                given_lanes_graph.add_edge(u, v, fixed_direction=True)

            if lane_properties.direction in [lanes.DIRECTION_BACKWARD, lanes.DIRECTION_BOTH]:
                given_lanes_graph.add_edge(v, u, fixed_direction=True)

            if lane_properties.direction in [lanes.DIRECTION_BOTH]:
                given_lanes_graph.add_edge(u, v, fixed_direction=False)

    return given_lanes_graph