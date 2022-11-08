from snman import osmnx as ox

ox.config(log_console=False, use_cache=True)

DIRECTION_FORWARD = '>'
DIRECTION_BACKWARD = '<'
DIRECTION_BOTH = '-'
DIRECTION_TBD = '?'

LANETYPE_MOTORIZED = 'M'        # A normal lane accessible to car, public transport, and cyclists
LANETYPE_DEDICATED_PT = 'T'     # Only for public transport
LANETYPE_CYCLING_PATH = 'P'     # Only for cyclists and possibly pedestrians
LANETYPE_CYCLING_LANE = 'L'     # Advisory cycling lane, in some cases also used by other traffic
LANETYPE_FOOT = 'F'             # Pedestrians only

KEY_LANES_DESCRIPTION = 'ln_desc'   # under which key of each edge is the existing lane configuration
KEY_REVERSED = '_reversed'


# > = unidirectional lane with defined direction
# ? = unidirectional lane with direction yet to be defined
# - = bidirectional lane (e.g. local streets with light traffic or cycling paths without lanes)
DEFAULT_LANE_WIDTHS = {

    LANETYPE_MOTORIZED + DIRECTION_FORWARD: 3,
    LANETYPE_MOTORIZED + DIRECTION_BACKWARD: 3,
    LANETYPE_MOTORIZED + DIRECTION_TBD: 3,
    LANETYPE_MOTORIZED + DIRECTION_BOTH: 4.5,

    LANETYPE_DEDICATED_PT + DIRECTION_FORWARD: 3,
    LANETYPE_DEDICATED_PT + DIRECTION_BACKWARD: 3,
    LANETYPE_DEDICATED_PT + DIRECTION_TBD: 3,
    LANETYPE_DEDICATED_PT + DIRECTION_BOTH: 4.5,

    LANETYPE_CYCLING_LANE + DIRECTION_FORWARD: 1.3,
    LANETYPE_CYCLING_LANE + DIRECTION_BACKWARD: 1.3,
    LANETYPE_CYCLING_LANE + DIRECTION_TBD: 1.3,
    LANETYPE_CYCLING_LANE + DIRECTION_BOTH: 2.6,

    LANETYPE_CYCLING_PATH + DIRECTION_FORWARD: 1.8,
    LANETYPE_CYCLING_PATH + DIRECTION_BACKWARD: 1.8,
    LANETYPE_CYCLING_PATH + DIRECTION_TBD: 1.8,
    LANETYPE_CYCLING_PATH + DIRECTION_BOTH: 2,

    LANETYPE_FOOT + DIRECTION_FORWARD: 1.8,
    LANETYPE_FOOT + DIRECTION_BACKWARD: 1.8,
    LANETYPE_FOOT + DIRECTION_TBD: 1.8,
    LANETYPE_FOOT + DIRECTION_BOTH: 2,

}