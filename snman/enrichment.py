from leuvenmapmatching.matcher.distance import DistanceMatcher
from leuvenmapmatching.map.inmem import InMemMap
from leuvenmapmatching import visualization as mmviz
import shapely as shp
from statistics import mean


def match_linestrings(G, source, column_configs, show_test_plot=None):
    """
    Make a spatial join of the graph edges and polylines in a GeoDataFrame.
    Copy selected attributes from the GeoFDataFrame to the graph edges.

    The spatial join is made using LeuvenMapMatching:
    https://github.com/wannesm/LeuvenMapMatching

    Parameters
    ----------
    G : nx.MultiGraph
        street graph, target
    source : gpd.GeoDataFrame
        data source
    column_configs : list
        a list of dictionaries, example:
            [
                {'source_column': 'DTV_ALLE',   'target_column': 'adt_avg',         'agg': 'avg' },
                {'source_column': 'DTV_ALLE',   'target_column': 'adt_max',         'agg': 'max' },
                {'source_column': 'FROMNODENO', 'target_column': 'npvm_fromnodeno', 'agg': 'list'},
                {'source_column': 'TONODENO',   'target_column': 'npvm_tonodeno',   'agg': 'list'}
            ]
    show_test_plot : bool
        make a test plot showing the map matching process,
        generated by the leuvenmapmatching library (for debugging)

    Returns
    -------
    None
    """

    map_con = InMemMap("source", use_latlon=False, use_rtree=True, index_edges=True, crs_xy=2056)

    # please note that lv works with lat, lon (reverse order)
    for id, data in G.nodes.items():
        map_con.add_node(id, (data['y'], data['x']))
        #print((data['y'], data['x']))

    for id, data in G.edges.items():
        u = int(id[0])
        v = int(id[1])
        # only include the edges that are accessible for cars, incl. the correct direction
        if 'M>' in data['ln_desc'] or 'M-' in data['ln_desc']:
            map_con.add_edge(u,v)
        if 'M<' in data['ln_desc'] or 'M-' in data['ln_desc']:
            map_con.add_edge(v,u)

    matcher = DistanceMatcher(map_con, max_dist=30, max_dist_init=30, max_lattice_width=5, non_emitting_states=True, only_edges=True)

    def _get_nodes_of_linestring(geom):
        if isinstance(geom, shp.geometry.MultiLineString):
            geom = geom.geoms[0]
        path = geom.coords
        path = [coords[::-1] for coords in path]
        matcher.match(path)
        nodes = matcher.path_pred_onlynodes
        #print(nodes)
        return nodes

    source['nodes'] = source.apply(lambda x: _get_nodes_of_linestring(x['geometry']), axis=1)

    for config in column_configs:

        edge_values = {}
        for index, edge in source.iterrows():
            value = edge[config['source_column']]
            nodes = edge['nodes']
            if len(nodes) < 2:
                continue
            node_pairs = [nodes[i:i+2] for i in range(len(nodes)-1)]
            for node_pair in node_pairs:
                u = node_pair[0]
                v = node_pair[1]
                if edge_values.get((u,v)) is None:
                    edge_values[(u,v)] = []
                edge_values[(u,v)].append(value)

        for id, data in G.edges.items():
            if config['agg'] == 'avg':
                data[config['target_column'] + '_forward']  = mean(edge_values.get(id[:2], [0]))
                data[config['target_column'] + '_backward'] = mean(edge_values.get(id[:2][::-1], [0]))
            if config['agg'] == 'max':
                data[config['target_column'] + '_forward']  = max(edge_values.get(id[:2], [0]))
                data[config['target_column'] + '_backward'] = max(edge_values.get(id[:2][::-1], [0]))
            elif config['agg'] == 'list':
                data[config['target_column'] + '_forward']  = str(edge_values.get(id[:2]))
                data[config['target_column'] + '_backward'] = str(edge_values.get(id[:2][::-1]))

    if show_test_plot is not None:
        source_test_path = source.query(show_test_plot).reset_index().iloc[0]['geometry']
        path = [coords[::-1] for coords in list(source_test_path.coords)]
        matcher.match(path)
        print(matcher.path_pred_onlynodes)
        mmviz.plot_map(map_con, matcher=matcher,show_labels=False, show_matching=True, show_graph=True)