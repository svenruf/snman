from .constants import *
import math
import networkx as nx
from . import utils


def generate_lanes(G, attr=KEY_LANES_DESCRIPTION):
    """
    Reverse-engineer the lanes of each street edge and store them as a list in an attribute

    Parameters
    ----------
    G : nx.MultiGraph
        street graph
    attr : str
        in which attribute should the lanes be stored

    Returns
    -------
    None
    """

    for edge in G.edges(data=True, keys=True):
        edge_data = edge[3]
        edge_data[attr] = _generate_lanes_for_edge(edge_data)


def _generate_lanes_for_edge(edge):
    """
    Reverse-engineer the lanes for one edge

    Resulting format: {lane type} + {lane direction}
        * lane type: see LANETYPE_* under .constants
        * lane direction: see DIRECTION_* under .constants
        * example: M> (lane for motorized traffic, forward)

    Parameters
    ----------
    edge : dict
        the data dictionary of an edge

    Returns
    -------
    lane_list : list
        a list of lanes, following the format described above
    """

    # PART 1: INITIALIZE VARIABLES

    # left/right lanes: cycling lanes that are not included in the osm lanes tag
    left_lanes_list = []
    forward_lanes_list = []
    both_dir_lanes_list = []
    backward_lanes_list = []
    right_lanes_list = []

    # Reverse forward/backward if the edge has been reversed in the conversion into undirected graph
    if edge.get(KEY_REVERSED, False) == True:
        _DIRECTION_FORWARD = DIRECTION_BACKWARD
        _DIRECTION_BACKWARD = DIRECTION_FORWARD
    else:
        _DIRECTION_FORWARD = DIRECTION_FORWARD
        _DIRECTION_BACKWARD = DIRECTION_BACKWARD

    # is this street oneway?
    oneway = edge.get('oneway', False) or edge.get('junction', False) == 'roundabout'

    # get the general lane count, fill in with default value according to the exact case
    if oneway:
        # 1 for all oneway streets
        n_lanes = int(edge.get('lanes', 1))
    elif edge.get('maxspeed', -1) < 50:
        # 1 for speeds below 50 kmh
        n_lanes = int(edge.get('lanes', 1))
    else:
        # 2 for faster roads
        n_lanes = int(edge.get('lanes', 2))

    # initialize detailed lane counts
    n_lanes_forward = int(edge.get('lanes:forward', 0))
    n_lanes_backward = int(edge.get('lanes:backward', 0))
    n_lanes_both = 0

    n_lanes_motorized = 0
    n_lanes_motorized_forward = 0
    n_lanes_motorized_backward = 0
    n_lanes_motorized_both = 0

    n_lanes_dedicated_pt = 0
    n_lanes_dedicated_pt_forward = 0
    n_lanes_dedicated_pt_backward = 0
    n_lanes_dedicated_pt_both = 0

    # PART 2: RECONSTRUCT LANE COUNTS

    # if forward/backward lanes are defined, make sure that the total lane count is consistent
    if n_lanes_forward or n_lanes_backward:
        n_lanes = max([n_lanes_forward + n_lanes_backward, n_lanes])

    # two-way street with more than 1 lane but no explicit lane counts forward/backward are defined
    if n_lanes > 1 and not oneway:
        n_lanes_forward = math.floor(n_lanes / 2)
        n_lanes_backward = math.ceil(n_lanes / 2)
    # two-way street with exactly one lane
    elif n_lanes == 1 and not oneway:
        n_lanes_both = 1
    # oneway street with n_lanes defined
    elif n_lanes > 0 and oneway:
        n_lanes_forward = n_lanes

    # If the edge is dedicated for public transport
    if (edge.get('highway') == 'service' or edge.get('access') == 'no') and (
            edge.get('psv') == 'yes' or edge.get('bus') == 'yes'):
        n_lanes_dedicated_pt = max([n_lanes, 2])
        n_lanes_dedicated_pt_forward = max([n_lanes_forward, 1])
        n_lanes_dedicated_pt_backward = max([n_lanes_backward, 1])
        n_lanes_dedicated_pt_both = 0
    else:
        n_lanes_motorized = n_lanes
        n_lanes_motorized_forward = n_lanes_forward
        n_lanes_motorized_backward = n_lanes_backward
        n_lanes_motorized_both = n_lanes_both

    # PART 3: GENERATE LANES

    # Cycleway [with walking]
    if edge.get('highway') in CYCLING_HIGHWAY_VALUES:
        # walking allowed without segregation
        if edge.get('foot') in {'yes', 'designated'} and edge.get('segregated') != 'yes':
            # oneway for cyclists
            if edge.get('oneway') in {'yes', 1} or edge.get('oneway:bicycle') in {'yes', 1}:
                both_dir_lanes_list.extend([LANETYPE_FOOT_CYCLING_MIXED + _DIRECTION_FORWARD])
            # both ways for cyclists
            else:
                both_dir_lanes_list.extend([LANETYPE_FOOT_CYCLING_MIXED + DIRECTION_BOTH])
        # walking allowed with segregation
        elif edge.get('foot') in {'yes', 'designated'} and edge.get('segregated') == 'yes':
            # oneway for cyclists
            if edge.get('oneway') in {'yes', 1} or edge.get('oneway:bicycle') in {'yes', 1}:
                both_dir_lanes_list.extend([LANETYPE_FOOT + DIRECTION_BOTH])
                forward_lanes_list.extend([LANETYPE_CYCLING_TRACK + _DIRECTION_FORWARD])
            # both ways for cyclists
            else:
                both_dir_lanes_list.extend([LANETYPE_FOOT + DIRECTION_BOTH])
                both_dir_lanes_list.extend([LANETYPE_CYCLING_TRACK + DIRECTION_BOTH])
        # walking not allowed
        else:
            # oneway for cyclists
            if edge.get('oneway') in {'yes', 1}:
                forward_lanes_list.extend([LANETYPE_CYCLING_TRACK + _DIRECTION_FORWARD])
            # both ways for cyclists
            else:
                both_dir_lanes_list.extend([LANETYPE_CYCLING_TRACK + DIRECTION_BOTH])

    # Walkway [with cycling]
    elif edge.get('highway') in PEDESTRIAN_HIGHWAY_VALUES:
        # cycling allowed without segregation
        if (edge.get('bicycle') in {'yes', 'designated'} or edge.get('bicycle:conditional')) \
                and edge.get('segregated') != 'yes':
            # oneway for cyclists
            if edge.get('oneway') in {'yes', 1} or edge.get('oneway:bicycle') in {'yes', 1}:
                both_dir_lanes_list.extend([LANETYPE_FOOT_CYCLING_MIXED + _DIRECTION_FORWARD])
            # both ways for cyclists
            else:
                both_dir_lanes_list.extend([LANETYPE_FOOT_CYCLING_MIXED + DIRECTION_BOTH])
        # cycling allowed with segregation
        elif (edge.get('bicycle') in {'yes', 'designated'} or edge.get('bicycle:conditional')) \
                and edge.get('segregated') == 'yes':
            # oneway for cyclists
            if edge.get('oneway') in {'yes', 1} or edge.get('oneway:bicycle') in {'yes', 1}:
                both_dir_lanes_list.extend([LANETYPE_FOOT + DIRECTION_BOTH])
                forward_lanes_list.extend([LANETYPE_CYCLING_TRACK + _DIRECTION_FORWARD])
            # both ways for cyclists
            else:
                both_dir_lanes_list.extend([LANETYPE_FOOT + DIRECTION_BOTH])
                both_dir_lanes_list.extend([LANETYPE_CYCLING_TRACK + DIRECTION_BOTH])
        # cycling not allowed
        else:
            both_dir_lanes_list.extend([LANETYPE_FOOT + DIRECTION_BOTH])

    # Normal road
    elif edge.get('highway') not in {'platform'}:
        # Add sidewalk left (inactive to prevent double sidewalks)
        # if edge.get('sidewalk') in {'left', 'both'}:
        #    left_lanes_list.extend([LANETYPE_FOOT + DIRECTION_BOTH])
        # Add cycling lane left
        if edge.get('cycleway:left') == 'lane' \
                or edge.get('cycleway:both') == 'lane' \
                or edge.get('cycleway') == 'lane':
            left_lanes_list.extend([LANETYPE_CYCLING_LANE + _DIRECTION_BACKWARD])

        # Add cycling lane right
        if edge.get('cycleway:right') == 'lane' \
                or edge.get('cycleway:both') == 'lane' \
                or edge.get('cycleway') == 'lane':
            right_lanes_list.extend([LANETYPE_CYCLING_LANE + _DIRECTION_FORWARD])
        # Add sidewalk right
        # if edge.get('sidewalk') in {'right', 'both'}:
        #    right_lanes_list.extend([LANETYPE_FOOT + DIRECTION_BOTH])

        backward_lanes_list.extend([LANETYPE_MOTORIZED + _DIRECTION_BACKWARD] * n_lanes_motorized_backward)
        backward_lanes_list.extend([LANETYPE_DEDICATED_PT + _DIRECTION_BACKWARD] * n_lanes_dedicated_pt_backward)

        both_dir_lanes_list.extend([LANETYPE_DEDICATED_PT + DIRECTION_BOTH] * n_lanes_dedicated_pt_both)
        both_dir_lanes_list.extend([LANETYPE_MOTORIZED + DIRECTION_BOTH] * n_lanes_motorized_both)

        forward_lanes_list.extend([LANETYPE_DEDICATED_PT + _DIRECTION_FORWARD] * n_lanes_dedicated_pt_forward)
        forward_lanes_list.extend([LANETYPE_MOTORIZED + _DIRECTION_FORWARD] * n_lanes_motorized_forward)

    # Everything else
    else:
        pass

    # PART 4: APPLY DEDICATED LANES BASED ON DETAILED LANE DESCRIPTIONS

    # apply bus lanes
    # first, try to use the "bus:lanes:*" tag. if not possible, use the "vehicle:lanes:*" tag
    # but never use both as this could lead to conflicts
    if edge.get('bus:lanes', edge.get('bus:lanes:forward')):
        osm_bus_lanes_forward = edge.get('bus:lanes', edge.get('bus:lanes:forward', '')).split('|')
        for i, lane in enumerate(osm_bus_lanes_forward):
            if lane == 'designated' and i < len(forward_lanes_list):
                forward_lanes_list[i] = LANETYPE_DEDICATED_PT + _DIRECTION_FORWARD

    else:
        osm_vehicle_lanes_forward = edge.get('vehicle:lanes:forward', '').split('|')
        for i, lane in enumerate(osm_vehicle_lanes_forward):
            if lane == 'no' and i < len(forward_lanes_list):
                forward_lanes_list[i] = LANETYPE_DEDICATED_PT + _DIRECTION_FORWARD

    # do the same in backward direction
    if edge.get('bus:lanes:backward'):
        osm_bus_lanes_backward = edge.get('bus:lanes:backward', '').split('|')
        # reverse the lane order because we are  still working in the forward direction
        osm_bus_lanes_backward.reverse()
        for i, lane in enumerate(osm_bus_lanes_backward):
            if lane == 'designated' and i < len(backward_lanes_list):
                backward_lanes_list[i] = LANETYPE_DEDICATED_PT + _DIRECTION_BACKWARD

    else:
        osm_vehicle_lanes_backward = edge.get('vehicle:lanes:backward', '').split('|')
        # reverse the lane order because we are still working in the forward direction
        osm_vehicle_lanes_backward.reverse()
        for i, lane in enumerate(osm_vehicle_lanes_backward):
            if lane == 'no' and i < len(backward_lanes_list):
                backward_lanes_list[i] = LANETYPE_DEDICATED_PT + _DIRECTION_BACKWARD

    # PART 5: RETURN

    # merge all pars of the road section
    return left_lanes_list + backward_lanes_list + both_dir_lanes_list + forward_lanes_list + right_lanes_list


def _reverse_lanes(lanes):
    """
    Reverse the order and direction of all lanes of an edge

    Parameters
    ----------
    lanes : list
        a list of lanes, following the format described under _generate_lanes_for_edge

    Returns
    -------
    reversed_lanes : list
        lanes, with reversed order and directions
    """
    reversed_lanes = lanes
    # We use >> and << as temporary symbols during the process
    reversed_lanes = [lane.replace(DIRECTION_FORWARD, '>>') for lane in reversed_lanes]
    reversed_lanes = [lane.replace(DIRECTION_BACKWARD, '<<') for lane in reversed_lanes]
    reversed_lanes = [lane.replace('>>', DIRECTION_BACKWARD) for lane in reversed_lanes]
    reversed_lanes = [lane.replace('<<', DIRECTION_FORWARD) for lane in reversed_lanes]
    reversed_lanes.reverse()
    return reversed_lanes


def reverse_lane(lane):
    lp = _lane_properties(lane)
    if lp.direction == DIRECTION_FORWARD:
        return lane.replace(DIRECTION_FORWARD, DIRECTION_BACKWARD)
    else:
        return lane.replace(DIRECTION_BACKWARD, DIRECTION_FORWARD)


def generate_lane_stats(G, lanes_attribute=KEY_LANES_DESCRIPTION):
    """
    Add lane statistics to all edges for the street graph

    Parameters
    ------
    G : nx.MultiGraph
        street graph
    lanes_attribute : str
        which attribute describing the lanes should be used
        (e.g., lanes in status quo or lanes after rebuilding)

    Returns
    -------
    None
    """

    for edge in G.edges(data=True, keys=True):
        edge_data = edge[3]
        _generate_lane_stats_for_edge(edge_data, lanes_attribute)


def _generate_lane_stats_for_edge(edge, lanes_attribute=KEY_LANES_DESCRIPTION):
    # TODO: Generate stats for both status quo and after rebuilding
    """
    Add lane statistics to one edge. Following attributes are added:
        * width_cycling_m -> total width for cycling in meters
        * width_motorized_m -> total width for motorized traffic in meters
        * width_total_m -> total width of all lanes
        * n_lanes_motorized -> number of lanes for motorized traffic

    Parameters
    ----------
    edge : dict
        the data dictionary of an edge
    lanes_attribute : str
        which attribute describing the lanes should be used
        (e.g., lanes in status quo or lanes after rebuilding)

    Returns
    -------
    None
    """

    lanes = edge.get(lanes_attribute, [])
    lane_stats = _lane_stats(lanes)

    width_cycling = 0
    width_motorized = 0
    width_total = 0

    for lane in lanes:
        lane_properties = _lane_properties(lane)
        if lane_properties.lanetype == LANETYPE_MOTORIZED:
            width_motorized += lane_properties.width
        if lane_properties.lanetype == LANETYPE_CYCLING_LANE:
            width_cycling += lane_properties.width
        width_total += lane_properties.width

    try:
        proportion_cycling = width_cycling / width_total
    except ZeroDivisionError:
        proportion_cycling = None

    # basic stats
    edge[lanes_attribute + '_width_cycling_m'] = width_cycling
    edge[lanes_attribute + '_width_motorized_m'] = width_motorized
    edge[lanes_attribute + '_width_total_m'] = width_total
    edge[lanes_attribute + '_n_lanes_motorized'] = lane_stats.n_lanes_motorized

    # description of best cycling option in each direction
    for user_dir_name, user_dir_description in {'forward': DIRECTION_FORWARD, 'backward': DIRECTION_BACKWARD}.items():
        for lane_direction in [user_dir_description, DIRECTION_BOTH]:
            for lanetype in CYCLING_QUALITY_HIERARCHY:
                lane_description = lanetype + lane_direction
                if lane_description in lanes:
                    edge[lanes_attribute + '_cycling_' + user_dir_name] = lane_description
                    break


class _lane_properties:
    """
    A class for a standardized set of properties of a lane
    """

    valid = None
    width = None
    lanetype = None
    direction = None
    motorized = None
    private_cars = None
    dedicated_pt = None
    dedicated_cycling = None
    dedicated_cycling_lane = None
    dedicated_cycling_track = None
    cycling_cost_factor = None
    primary_mode = None
    modes = None

    def __init__(self, lane_description):
        """
        Decodes a lane into a set of standardized properties

        Parameters
        ----------
        lane_description : str
            description of a lane following the format described in _generate_lanes_for_edge
        """

        if lane_description not in LANE_TYPES:
            self.valid = False

        else:
            self.valid = True
            self.width = LANE_TYPES[lane_description]['width']
            self.lanetype = lane_description[0:-1]
            self.direction = lane_description[-1]
            self.motorized = lane_description[0:-1] in [LANETYPE_MOTORIZED, LANETYPE_DEDICATED_PT]
            self.private_cars = lane_description[0:-1] == LANETYPE_MOTORIZED
            self.dedicated_pt = lane_description[0:-1] == LANETYPE_DEDICATED_PT
            self.dedicated_cycling = lane_description[0:-1] in \
                [LANETYPE_CYCLING_TRACK, LANETYPE_CYCLING_LANE, LANETYPE_FOOT_CYCLING_MIXED]
            self.dedicated_cycling_lane = lane_description[0:-1] == LANETYPE_CYCLING_LANE
            self.dedicated_cycling_track = lane_description[0:-1] == LANETYPE_CYCLING_TRACK
            self.cycling_cost_factor = LANE_TYPES[lane_description]['cycling_cost_factor']

            if self.private_cars:
                self.primary_mode = MODE_PRIVATE_CARS
            elif self.dedicated_pt:
                self.primary_mode = MODE_TRANSIT
            elif self.dedicated_cycling:
                self.primary_mode = MODE_CYCLING
            elif lane_description[0:-1] == LANETYPE_FOOT:
                self.primary_mode = MODE_FOOT

            self.modes = LANE_TYPES[lane_description]['modes']


class _lane_stats:
    """
    A class for a standardized set of statistics over all lanes
    """

    n_lanes_motorized_forward = 0
    n_lanes_motorized_backward = 0
    n_lanes_motorized_both_ways = 0
    n_lanes_motorized_direction_tbd = 0

    n_lanes_private_cars_forward = 0
    n_lanes_private_cars_backward = 0
    n_lanes_private_cars_both_ways = 0
    n_lanes_private_cars_direction_tbd = 0

    n_lanes_dedicated_pt_forward = 0
    n_lanes_dedicated_pt_backward = 0
    n_lanes_dedicated_pt_both_ways = 0
    n_lanes_dedicated_pt_direction_tbd = 0

    n_lanes_dedicated_cycling_lanes_forward = 0
    n_lanes_dedicated_cycling_lanes_backward = 0
    n_lanes_dedicated_cycling_lanes_both_ways = 0
    n_lanes_dedicated_cycling_lanes_direction_tbd = 0

    n_lanes_dedicated_cycling_tracks_forward = 0
    n_lanes_dedicated_cycling_tracks_backward = 0
    n_lanes_dedicated_cycling_tracks_both_ways = 0
    n_lanes_dedicated_cycling_tracks_direction_tbd = 0

    def __init__(self, lanes_description):
        """
        Decodes a list of lanes into a set of statistics

        Parameters
        ----------
        lanes_description : list
            a list of lanes following the format described in _generate_lanes_for_edge
        """

        for lane in lanes_description:
            lane_properties = _lane_properties(lane)
            direction = lane_properties.direction

            # Motorized Lanes
            if lane_properties.motorized:
                if direction == DIRECTION_FORWARD:
                    self.n_lanes_motorized_forward += 1
                elif direction == DIRECTION_BACKWARD:
                    self.n_lanes_motorized_backward += 1
                elif direction == DIRECTION_BOTH:
                    self.n_lanes_motorized_both_ways += 1
                elif direction == DIRECTION_TBD:
                    self.n_lanes_motorized_direction_tbd += 1

            # Private cars
            if lane_properties.private_cars:
                if direction == DIRECTION_FORWARD:
                    self.n_lanes_private_cars_forward += 1
                elif direction == DIRECTION_BACKWARD:
                    self.n_lanes_private_cars_backward += 1
                elif direction == DIRECTION_BOTH:
                    self.n_lanes_private_cars_both_ways += 1
                elif direction == DIRECTION_TBD:
                    self.n_lanes_private_cars_direction_tbd += 1

            # PT lanes
            if lane_properties.dedicated_pt:
                if direction == DIRECTION_FORWARD:
                    self.n_lanes_dedicated_pt_forward += 1
                if direction == DIRECTION_BACKWARD:
                    self.n_lanes_dedicated_pt_backward += 1
                if direction == DIRECTION_BOTH:
                    self.n_lanes_dedicated_pt_both_ways += 1
                if direction == DIRECTION_TBD:
                    self.n_lanes_dedicated_pt_direction_tbd += 1

            # Cycling lanes
            if lane_properties.dedicated_cycling_lane:
                if direction == DIRECTION_FORWARD:
                    self.n_lanes_dedicated_cycling_lanes_forward += 1
                elif direction == DIRECTION_BACKWARD:
                    self.n_lanes_dedicated_cycling_lanes_backward += 1
                elif direction == DIRECTION_BOTH:
                    self.n_lanes_dedicated_cycling_lanes_both_ways += 1
                elif direction == DIRECTION_TBD:
                    self.n_lanes_dedicated_cycling_lanes_direction_tbd += 1

            # Cycling paths
            if lane_properties.dedicated_cycling_track:
                if direction == DIRECTION_FORWARD:
                    self.n_lanes_dedicated_cycling_tracks_forward += 1
                elif direction == DIRECTION_BACKWARD:
                    self.n_lanes_dedicated_cycling_tracks_backward += 1
                elif direction == DIRECTION_BOTH:
                    self.n_lanes_dedicated_cycling_tracks_both_ways += 1
                elif direction == DIRECTION_TBD:
                    self.n_lanes_dedicated_cycling_tracks_direction_tbd += 1

        self.n_lanes_motorized = \
            self.n_lanes_motorized_forward + self.n_lanes_motorized_backward \
            + self.n_lanes_motorized_both_ways + self.n_lanes_motorized_direction_tbd


def update_osm_tags(G, lanes_description_key=KEY_LANES_DESCRIPTION):
    """
    Update the osm tags of all edges to match their current lanes. This is necessary after the simplification when
    multiple edges are merged into single edge

    Parameters
    ----------
    G : nx.MultiGraph
        street graph
    lanes_description_key : str
        which attribute should be used as a source of lane data

    Returns
    -------
    None
    """
    for edge in G.edges(data=True, keys=True):
        _update_osm_tags_for_edge(edge, lanes_description_key)


def _update_osm_tags_for_edge(edge, lanes_description_key):
    """
    Update OSM tags of one edge to match its current lanes

    Parameters
    ----------
    edge
    lanes_description_key

    Returns
    -------
    None
    """

    data = edge[3]
    lane_stats = _lane_stats(data.get(lanes_description_key, []))

    # Clean the tags before updating
    data['lanes'] = None
    data['lanes:forward'] = None
    data['lanes:backward'] = None
    data['lanes:both_ways'] = None
    data['oneway'] = None

    # Motorized lanes
    if lane_stats.n_lanes_motorized:
        data['lanes'] = lane_stats.n_lanes_motorized
    if lane_stats.n_lanes_motorized_forward:
        data['lanes:forward'] = lane_stats.n_lanes_motorized_forward
    if lane_stats.n_lanes_motorized_backward:
        data['lanes:backward'] = lane_stats.n_lanes_motorized_backward
    if lane_stats.n_lanes_motorized_both_ways > 0:
        data['lanes:both_ways'] = lane_stats.n_lanes_motorized_both_ways

    if (
        lane_stats.n_lanes_motorized_forward > 0
        and lane_stats.n_lanes_motorized_backward + lane_stats.n_lanes_motorized_both_ways == 0
    ):
        data['oneway'] = 'yes'
    elif (
        lane_stats.n_lanes_motorized_backward > 0
        and lane_stats.n_lanes_motorized_forward + lane_stats.n_lanes_motorized_both_ways == 0
    ):
        data['oneway'] = '-1'
    else:
        data['oneway'] = 'no'

    # Clean the tags before updating
    data['bus:lanes:backward'] = None
    data['bus:lanes:forward'] = None
    data['vehicle:lanes:backward'] = None
    data['vehicle:lanes:forward'] = None

    # PT lanes
    if lane_stats.n_lanes_dedicated_pt_both_ways > 0 or lane_stats.n_lanes_dedicated_pt_backward > 0:
        data['bus:lanes:backward'] = '|'.join(
            ['designated'] * lane_stats.n_lanes_dedicated_pt_both_ways +
            ['designated'] * lane_stats.n_lanes_dedicated_pt_backward +
            ['permissive'] * lane_stats.n_lanes_private_cars_both_ways +
            ['permissive'] * lane_stats.n_lanes_private_cars_backward
        )
        data['vehicle:lanes:backward'] = '|'.join(
            ['no'] * lane_stats.n_lanes_dedicated_pt_both_ways +
            ['no'] * lane_stats.n_lanes_dedicated_pt_backward +
            ['yes'] * lane_stats.n_lanes_private_cars_both_ways +
            ['yes'] * lane_stats.n_lanes_private_cars_backward
        )

    if lane_stats.n_lanes_dedicated_pt_both_ways > 0 or lane_stats.n_lanes_dedicated_pt_forward > 0:
        data['bus:lanes:forward'] = '|'.join(
            ['designated'] * lane_stats.n_lanes_dedicated_pt_both_ways +
            ['designated'] * lane_stats.n_lanes_dedicated_pt_forward +
            ['permissive'] * lane_stats.n_lanes_private_cars_both_ways +
            ['permissive'] * lane_stats.n_lanes_private_cars_forward
        )
        data['vehicle:lanes:forward'] = '|'.join(
            ['no'] * lane_stats.n_lanes_dedicated_pt_both_ways +
            ['no'] * lane_stats.n_lanes_dedicated_pt_forward +
            ['yes'] * lane_stats.n_lanes_private_cars_both_ways +
            ['yes'] * lane_stats.n_lanes_private_cars_forward
        )

    # Clean the tags before updating
    data['cycleway'] = None
    data['cycleway:lane'] = None
    data['cycleway:right'] = None
    data['cycleway:right:lane'] = None
    data['cycleway:left'] = None
    data['cycleway:left:lane'] = None

    # Cycling lanes
    if lane_stats.n_lanes_dedicated_cycling_lanes_both_ways > 0 \
            or (
            lane_stats.n_lanes_dedicated_cycling_lanes_forward > 0 and lane_stats.n_lanes_dedicated_cycling_lanes_backward > 0):
        # both directions
        data['cycleway'] = 'lane'
        data['cycleway:lane'] = 'advisory'
    elif lane_stats.n_lanes_dedicated_cycling_lanes_forward > 0:
        # only forward
        data['cycleway:right'] = 'lane'
        data['cycleway:right:lane'] = 'advisory'
    elif lane_stats.n_lanes_dedicated_cycling_lanes_backward > 0:
        # only backward
        data['cycleway:left'] = 'lane'
        data['cycleway:left:lane'] = 'advisory'

    # Cycling tracks
    if lane_stats.n_lanes_dedicated_cycling_tracks_both_ways > 0 \
            or (
            lane_stats.n_lanes_dedicated_cycling_tracks_forward > 0 and lane_stats.n_lanes_dedicated_cycling_tracks_backward > 0):
        # both directions
        data['cycleway'] = 'track'
    elif lane_stats.n_lanes_dedicated_cycling_tracks_forward > 0:
        # only forward
        data['cycleway:right'] = 'track'
    elif lane_stats.n_lanes_dedicated_cycling_tracks_backward > 0:
        # only backward
        data['cycleway:left'] = 'track'

    maxspeed = data.get('maxspeed', -1)
    if maxspeed == -1 and 'maxspeed' in data:
        del data['maxspeed']


def _is_backward_oneway_street(lanes):
    """
    Returns true if the given lane configuration represents a one-way street that is digitized in opposite direction.
    This is needed for preparing the graph for osm export where one-way streets are typically digitized
    in the forward direction.

    Parameters
    ----------
    lanes: list
        a list of lanes following the format described in _generate_lanes_for_edge

    Returns
    -------
    bool
    """

    ls = _lane_stats(lanes)

    # only motorized lanes backward
    if (
            ls.n_lanes_motorized_forward == 0
            and ls.n_lanes_motorized_both_ways == 0
            and ls.n_lanes_motorized_direction_tbd == 0
            and ls.n_lanes_motorized_backward > 0
    ):
        return True
    else:
        return False


def reorder_lanes(G, lanes_attribute=KEY_LANES_DESCRIPTION):

    for id, data in G.edges.items():
        data[lanes_attribute] = _reorder_lanes_on_edge(data[lanes_attribute])


def _reorder_lanes_on_edge(lanes):
    """
    Reorder the lane list of an edge

    Parameters
    ----------
    lanes : list

    Returns
    -------
    list
    """

    # prepare the data structure
    sorted_lanes = {}
    for mode in MODES:
        sorted_lanes[mode] = {}
        for direction in DIRECTIONS:
            sorted_lanes[mode][direction] = []

    # sort by primary mode and direction
    for i, l in enumerate(lanes):
        lp = _lane_properties(l)
        sorted_lanes[lp.primary_mode][lp.direction].append(l)

    # decide between cycling lanes and cycling paths
    for direction in DIRECTIONS:

        cycling_lanes = sorted_lanes[MODE_CYCLING][direction]
        n_lanes_cycling = len(cycling_lanes)
        n_lanes_foot_and_cycling = 0
        n_lanes_foot = 0
        n_motorized_lanes = len(
            list(utils.flatten_list(sorted_lanes[MODE_PRIVATE_CARS].values())) +
            list(utils.flatten_list(sorted_lanes[MODE_TRANSIT].values()))
        )

        # if there is at least one mixed cycling/foot lane and at the same time other cycling lane then convert one
        # mixed lane to a pure footway
        mixed = list(filter(lambda x: _lane_properties(x).lanetype == LANETYPE_FOOT_CYCLING_MIXED, cycling_lanes))
        if len(mixed) >= 1 and n_lanes_cycling >= 2:
            n_lanes_cycling -= 1
            n_lanes_foot += 1
        elif len(mixed) >= 1:
            n_lanes_cycling -= 1
            n_lanes_foot_and_cycling += 1

        # streets with wide cycling space or without motorized traffic -> track
        if n_lanes_cycling > 1 or n_motorized_lanes == 0:
            lanetype = LANETYPE_CYCLING_TRACK

        # else -> cycling lane
        else:
            lanetype = LANETYPE_CYCLING_LANE

        sorted_lanes[MODE_CYCLING][direction] =\
            [lanetype + direction] * n_lanes_cycling +\
            [LANETYPE_FOOT_CYCLING_MIXED + direction] * n_lanes_foot_and_cycling
        sorted_lanes[MODE_FOOT][direction] = [LANETYPE_FOOT + DIRECTION_BOTH] * n_lanes_foot

    # order on the street
    return list(utils.flatten_list([

        sorted_lanes[MODE_CYCLING][DIRECTION_BACKWARD],
        sorted_lanes[MODE_PRIVATE_CARS][DIRECTION_BACKWARD],
        sorted_lanes[MODE_TRANSIT][DIRECTION_BACKWARD],

        sorted_lanes[MODE_TRANSIT][DIRECTION_BOTH],
        sorted_lanes[MODE_PRIVATE_CARS][DIRECTION_BOTH],
        sorted_lanes[MODE_CYCLING][DIRECTION_BOTH],

        sorted_lanes[MODE_TRANSIT][DIRECTION_FORWARD],
        sorted_lanes[MODE_PRIVATE_CARS][DIRECTION_FORWARD],
        sorted_lanes[MODE_CYCLING][DIRECTION_FORWARD],

        sorted_lanes[MODE_FOOT][DIRECTION_BOTH]

    ]))
