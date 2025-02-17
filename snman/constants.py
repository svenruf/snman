import osmnx as ox

ox.config(log_console=False, use_cache=True)

DIRECTION_FORWARD = '>'
DIRECTION_BACKWARD = '<'
DIRECTION_BOTH = '-'
DIRECTION_TBD = '?'
DIRECTIONS = [DIRECTION_FORWARD, DIRECTION_BACKWARD, DIRECTION_BOTH, DIRECTION_TBD]

MODE_FOOT = 'foot'
MODE_CYCLING = 'cycling'
MODE_PRIVATE_CARS = 'private_cars'
MODE_TRANSIT = 'transit'
MODES = {MODE_FOOT, MODE_CYCLING, MODE_PRIVATE_CARS, MODE_TRANSIT}
ACTIVE_MODES = {MODE_FOOT, MODE_CYCLING}
MOTORIZED_MODES = {MODE_PRIVATE_CARS, MODE_TRANSIT}

LANETYPE_MOTORIZED = 'M'            # A normal lane accessible to car, public transport, and cyclists
LANETYPE_DEDICATED_PT = 'T'         # Only for public transport
LANETYPE_CYCLING_TRACK = 'P'        # Only for cyclists and separated from other modes
LANETYPE_CYCLING_LANE = 'L'         # Advisory cycling lane, in some cases also used by other traffic
LANETYPE_CYCLING_PSEUDO = 'S'       # Contraflow cycling in one-way streets without cycling infrastructure
LANETYPE_FOOT_CYCLING_MIXED = 'X'   # Mixed, for cyclists and pedestrians
LANETYPE_FOOT = 'F'                 # Pedestrians only

# For assessing cycling quality, from best to worst
# TODO: To be replaced with ranking according to cycling comfort factors
CYCLING_QUALITY_HIERARCHY = [
    LANETYPE_CYCLING_TRACK,
    LANETYPE_FOOT_CYCLING_MIXED,
    LANETYPE_CYCLING_LANE,
    LANETYPE_MOTORIZED,
    LANETYPE_CYCLING_PSEUDO
]

# For sorting lanes in the crosssection
# TODO: To be replaced by sorting heuristics
LANETYPE_ORDER = ['T', 'M', 'L', 'P', 'S', 'F']
DIRECTION_ORDER = ['<', '-', '>']

KEY_LANES_DESCRIPTION = 'ln_desc'               # under which key is the existing lane configuration
KEY_LANES_DESCRIPTION_AFTER = 'ln_desc_after'   # under which key is the lane configuration after rebuilding
KEY_GIVEN_LANES_DESCRIPTION = 'given_lanes'
KEY_REVERSED = '_reversed'          # which key tells if the edge has been reversed

# in meters
# TODO: deprecated and will be removed later, use LANE_TYPES instead
DEFAULT_LANE_WIDTHS = {

    LANETYPE_MOTORIZED + DIRECTION_FORWARD: 3,
    LANETYPE_MOTORIZED + DIRECTION_BACKWARD: 3,
    LANETYPE_MOTORIZED + DIRECTION_TBD: 3,
    LANETYPE_MOTORIZED + DIRECTION_BOTH: 4.5,

    LANETYPE_DEDICATED_PT + DIRECTION_FORWARD: 3,
    LANETYPE_DEDICATED_PT + DIRECTION_BACKWARD: 3,
    LANETYPE_DEDICATED_PT + DIRECTION_TBD: 3,
    LANETYPE_DEDICATED_PT + DIRECTION_BOTH: 4.5,

    LANETYPE_CYCLING_LANE + DIRECTION_FORWARD: 1.5,
    LANETYPE_CYCLING_LANE + DIRECTION_BACKWARD: 1.5,
    LANETYPE_CYCLING_LANE + DIRECTION_TBD: 1.5,
    LANETYPE_CYCLING_LANE + DIRECTION_BOTH: 2,

    LANETYPE_CYCLING_TRACK + DIRECTION_FORWARD: 1.5,
    LANETYPE_CYCLING_TRACK + DIRECTION_BACKWARD: 1.5,
    LANETYPE_CYCLING_TRACK + DIRECTION_TBD: 1.5,
    LANETYPE_CYCLING_TRACK + DIRECTION_BOTH: 2,

    LANETYPE_CYCLING_PSEUDO + DIRECTION_FORWARD: 0,
    LANETYPE_CYCLING_PSEUDO + DIRECTION_BACKWARD: 0,
    LANETYPE_CYCLING_PSEUDO + DIRECTION_TBD: 0,
    LANETYPE_CYCLING_PSEUDO + DIRECTION_BOTH: 0,

    LANETYPE_FOOT_CYCLING_MIXED + DIRECTION_FORWARD: 2.5,
    LANETYPE_FOOT_CYCLING_MIXED + DIRECTION_BACKWARD: 2.5,
    LANETYPE_FOOT_CYCLING_MIXED + DIRECTION_TBD: 2.5,
    LANETYPE_FOOT_CYCLING_MIXED + DIRECTION_BOTH: 2.5,

    LANETYPE_FOOT + DIRECTION_FORWARD: 1.8,
    LANETYPE_FOOT + DIRECTION_BACKWARD: 1.8,
    LANETYPE_FOOT + DIRECTION_TBD: 1.8,
    LANETYPE_FOOT + DIRECTION_BOTH: 1.8,

}

LANE_TYPES = {
    LANETYPE_MOTORIZED + DIRECTION_FORWARD:
        {'width': 3.0, 'cycling_cost_factor': 1.0, 'modes': {MODE_PRIVATE_CARS, MODE_TRANSIT, MODE_CYCLING, MODE_FOOT}},
    LANETYPE_MOTORIZED + DIRECTION_BACKWARD:
        {'width': 3.0, 'cycling_cost_factor': 1.0, 'modes': {MODE_PRIVATE_CARS, MODE_TRANSIT, MODE_CYCLING, MODE_FOOT}},
    LANETYPE_MOTORIZED + DIRECTION_TBD:
        {'width': 3.0, 'cycling_cost_factor': 1.0, 'modes': {MODE_PRIVATE_CARS, MODE_TRANSIT, MODE_CYCLING, MODE_FOOT}},
    LANETYPE_MOTORIZED + DIRECTION_BOTH:
        {'width': 4.5, 'cycling_cost_factor': 1.0, 'modes': {MODE_PRIVATE_CARS, MODE_TRANSIT, MODE_CYCLING, MODE_FOOT}},

    LANETYPE_DEDICATED_PT + DIRECTION_FORWARD:
        {'width': 3.0, 'cycling_cost_factor': 1.0, 'modes': {MODE_TRANSIT}},
    LANETYPE_DEDICATED_PT + DIRECTION_BACKWARD:
        {'width': 3.0, 'cycling_cost_factor': 1.0, 'modes': {MODE_TRANSIT}},
    LANETYPE_DEDICATED_PT + DIRECTION_TBD:
        {'width': 3.0, 'cycling_cost_factor': 1.0, 'modes': {MODE_TRANSIT}},
    LANETYPE_DEDICATED_PT + DIRECTION_BOTH:
        {'width': 4.5, 'cycling_cost_factor': 1.0, 'modes': {MODE_TRANSIT}},

    LANETYPE_CYCLING_LANE + DIRECTION_FORWARD:
        {'width': 1.5, 'cycling_cost_factor': 0.5, 'modes': {MODE_CYCLING}},
    LANETYPE_CYCLING_LANE + DIRECTION_BACKWARD:
        {'width': 1.5, 'cycling_cost_factor': 0.5, 'modes': {MODE_CYCLING}},
    LANETYPE_CYCLING_LANE + DIRECTION_TBD:
        {'width': 1.5, 'cycling_cost_factor': 0.5, 'modes': {MODE_CYCLING}},
    LANETYPE_CYCLING_LANE + DIRECTION_BOTH:
        {'width': 2.0, 'cycling_cost_factor': 0.5, 'modes': {MODE_CYCLING}},

    LANETYPE_CYCLING_TRACK + DIRECTION_FORWARD:
        {'width': 1.5, 'cycling_cost_factor': 0.5, 'modes': {MODE_CYCLING}},
    LANETYPE_CYCLING_TRACK + DIRECTION_BACKWARD:
        {'width': 1.5, 'cycling_cost_factor': 0.5, 'modes': {MODE_CYCLING}},
    LANETYPE_CYCLING_TRACK + DIRECTION_TBD:
        {'width': 1.5, 'cycling_cost_factor': 0.5, 'modes': {MODE_CYCLING}},
    LANETYPE_CYCLING_TRACK + DIRECTION_BOTH:
        {'width': 2.5, 'cycling_cost_factor': 0.5, 'modes': {MODE_CYCLING}},

    LANETYPE_CYCLING_PSEUDO + DIRECTION_FORWARD:
        {'width': 0.0, 'cycling_cost_factor': 1.0, 'modes': {MODE_CYCLING}},
    LANETYPE_CYCLING_PSEUDO + DIRECTION_BACKWARD:
        {'width': 0.0, 'cycling_cost_factor': 1.0, 'modes': {MODE_CYCLING}},
    LANETYPE_CYCLING_PSEUDO + DIRECTION_TBD:
        {'width': 0.0, 'cycling_cost_factor': 1.0, 'modes': {MODE_CYCLING}},
    LANETYPE_CYCLING_PSEUDO + DIRECTION_BOTH:
        {'width': 0.0, 'cycling_cost_factor': 1.0, 'modes': {MODE_CYCLING}},

    LANETYPE_FOOT_CYCLING_MIXED + DIRECTION_FORWARD:
        {'width': 2.5, 'cycling_cost_factor': 0.5, 'modes': {MODE_CYCLING, MODE_FOOT}},
    LANETYPE_FOOT_CYCLING_MIXED + DIRECTION_BACKWARD:
        {'width': 2.5, 'cycling_cost_factor': 0.5, 'modes': {MODE_CYCLING, MODE_FOOT}},
    LANETYPE_FOOT_CYCLING_MIXED + DIRECTION_TBD:
        {'width': 2.5, 'cycling_cost_factor': 0.5, 'modes': {MODE_CYCLING, MODE_FOOT}},
    LANETYPE_FOOT_CYCLING_MIXED + DIRECTION_BOTH:
        {'width': 2.5, 'cycling_cost_factor': 0.5, 'modes': {MODE_CYCLING, MODE_FOOT}},

    LANETYPE_FOOT + DIRECTION_FORWARD:
        {'width': 1.8, 'cycling_cost_factor': 1.0, 'modes': {MODE_FOOT}},
    LANETYPE_FOOT + DIRECTION_BACKWARD:
        {'width': 1.8, 'cycling_cost_factor': 1.0, 'modes': {MODE_FOOT}},
    LANETYPE_FOOT + DIRECTION_TBD:
        {'width': 1.8, 'cycling_cost_factor': 1.0, 'modes': {MODE_FOOT}},
    LANETYPE_FOOT + DIRECTION_BOTH:
        {'width': 1.8, 'cycling_cost_factor': 1.0, 'modes': {MODE_FOOT}},
}

# Which highway=* values represent different infrastructures (primarily) for pedestrians and cyclists
PEDESTRIAN_HIGHWAY_VALUES = {'footway', 'path', 'track', 'pedestrian', 'steps'}
CYCLING_HIGHWAY_VALUES = {'cycleway'}
ACTIVE_HIGHWAY_VALUES = PEDESTRIAN_HIGHWAY_VALUES.union(CYCLING_HIGHWAY_VALUES)

OSM_TAGS = {
    'bridge', 'tunnel', 'layer', 'oneway', 'oneway:bicycle', 'ref', 'name',
    'highway', 'maxspeed', 'service', 'access', 'area',
    'landuse', 'width', 'est_width', 'junction', 'surface',
    'lanes', 'lanes:forward', 'lanes:backward',
    'cycleway', 'cycleway:both', 'cycleway:left', 'cycleway:right',
    'bicycle', 'bicycle:conditional',
    'sidewalk', 'sidewalk:left', 'sidewalk:right', 'foot',
    'psv', 'bus', 'bus:lanes', 'bus:lanes:forward', 'bus:lanes:backward',
    'vehicle:lanes:backward', 'vehicle:lanes:forward',
    'footway'
}

OSM_FILTER = [
    (
        f'["highway"]["area"!~"yes"]["access"!~"private"]'
        f'["highway"!~"abandoned|bridleway|bus_guideway|corridor|elevator|'
        f'escalator|planned|platform|proposed|raceway|construction|footway|pedestrian|steps|path"]'
        f'["service"!~"alley|driveway|emergency_access|parking|parking_aisle|private"]'
        f'["access"!~"no"]'
    ),
    (
        f'["highway"]["bicycle"]["bicycle"!~"no"]["area"!~"yes"]'
        f'["highway"!~"abandoned|bridleway|bus_guideway|corridor|elevator|'
        f'escalator|planned|platform|proposed|raceway|construction"]'
    ),
    (
        f'["highway"]["bicycle:conditional"]["area"!~"yes"]'
        f'["highway"!~"abandoned|bridleway|bus_guideway|corridor|elevator|'
        f'escalator|planned|platform|proposed|raceway|construction"]'
    ),
    (
        f'["highway"]["bus"="yes"]["area"!~"yes"]'
        f'["highway"!~"abandoned|bridleway|bus_guideway|corridor|elevator|'
        f'escalator|planned|platform|proposed|raceway|construction"]'
    ),
    (
        f'["highway"]["psv"="yes"]["area"!~"yes"]'
        f'["highway"!~"abandoned|bridleway|bus_guideway|corridor|elevator|'
        f'escalator|planned|platform|proposed|raceway|construction"]'
    ),
    # pedestrian paths incl. those mapped as area
    #(
    #    f'["highway"="footway|pedestrian"]'
    #    f'["highway"!~"abandoned|bridleway|bus_guideway|corridor|elevator|'
    #    f'escalator|planned|platform|proposed|raceway|construction"]'
    #)
]

CRS = 'epsg:2056'

EXPORT_EDGE_COLUMNS = [
    'grade',
    'ln_desc',
    'width_total_m',
    'width_motorized_m',
    'length',
    'n_lanes_motorized',
    'cycling_forward',
    'cycling_backward',
    'maxspeed',
    'highway',
    'hierarchy',
    'layer',
    'adt_max_forward',
    'adt_max_backward',
    'adt_avg_forward',
    'adt_avg_backward'
]