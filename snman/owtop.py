import networkx as nx
from . import constants, utils, distribution
from . import osmnx_customized as oxc


def rebuild_regions(
        G,
        rebuilding_regions_gdf,
        source_lanes_attribute=constants.KEY_LANES_DESCRIPTION,
        target_lanes_attribute=constants.KEY_LANES_DESCRIPTION_AFTER,
        initialize_target_lanes_attribute=True,
        **kwargs
):
    """
    Rebuild parts of the street graph in all "rebuilding regions"

    Parameters
    ----------
    G : nx.MultiGraph
        street graph
    rebuilding_regions_gdf : gpd.GeoDataFrame
        see .io.load_rebuilding_regions
    source_lanes_attribute : str
        attribute holding the lanes that should be used as input
    target_lanes_attribute : str
        attribute holding the lanes that should be used as output
    initialize_target_lanes_attribute : bool
        reset the rebuilt lane configurations before starting
    kwargs
        see link_elimination

    Returns
    -------
    None
    """

    if initialize_target_lanes_attribute:
        nx.set_edge_attributes(
            G,
            nx.get_edge_attributes(G, source_lanes_attribute),
            target_lanes_attribute
        )

    for idx, data in rebuilding_regions_gdf[rebuilding_regions_gdf['active'] == True].iterrows():
        _rebuild_region(
            G,
            data['geometry'],
            data['hierarchies_to_include'],
            data['hierarchies_to_fix'],
            source_lanes_attribute=target_lanes_attribute,  # chaining by taking target attribute as a source
            target_lanes_attribute=target_lanes_attribute,
            keep_all_streets=data['keep_all_streets'],
            **kwargs
        )


def _rebuild_region(
        G,
        polygon,
        hierarchies_to_include,
        hierarchies_to_fix,
        source_lanes_attribute=constants.KEY_LANES_DESCRIPTION,
        target_lanes_attribute=constants.KEY_LANES_DESCRIPTION_AFTER,
        **kwargs
):
    """
    Rebuild part of the street graph within a polygon

    Parameters
    ----------
    G : nx.MultiGraph
        street graph
    polygon : shp.geometry.Polygon
        which part of the street graph should be rebuilt
    hierarchies_to_include : list
        which hierarchies of streets should be considered in the process, include all streets if empty
    hierarchies_to_fix : list
        which hierarchies of streets should be left unchanged
    source_lanes_attribute : str
        attribute holding the lanes that should be used as input
    target_lanes_attribute : str
        attribute holding the lanes that should be used as output
    kwargs
        see link_elimination

    Returns
    -------
    None
    """

    # create a subgraph with only those edges that should be reorganized
    H = oxc.truncate.truncate_graph_polygon(G, polygon, quadrat_width=100, retain_all=True)

    if len(H.edges) == 0:
        return

    if len(hierarchies_to_include) > 0:
        filtered_edges = dict(filter(lambda key_value: key_value[1]['hierarchy']
            not in hierarchies_to_include, H.edges.items()))
        H.remove_edges_from(filtered_edges.keys())

    # initialize the input for link elimination
    H_minimal_graph_input = distribution.create_given_lanes_graph(
        H,
        hierarchies_to_fix=hierarchies_to_fix,
        source_lanes_attribute=source_lanes_attribute
    )
    #snman.export_streetgraph(H_minimal_graph_input, export_path + 'given_lanes.gpkg', export_path + 'given_lanes_nodes.gpkg')

    # run the link elimination
    H_minimal_graph_output = link_elimination(H_minimal_graph_input, **kwargs)
    #snman.export_streetgraph(H_minimal_graph_output, export_path + 'minimal_graph_out_edges.gpkg', export_path + 'minimal_graph_out_nodes.gpkg')

    # apply the link elimination output to the subgraph graph
    rebuild_lanes_from_owtop_graph(
        H,
        H_minimal_graph_output,
        hierarchies_to_protect=hierarchies_to_fix,
        source_lanes_attribute=source_lanes_attribute,
        target_lanes_attribute=target_lanes_attribute
    )

    # write the reorganized lanes from subgraph H into the main graph G
    nx.set_edge_attributes(G, nx.get_edge_attributes(H, target_lanes_attribute), target_lanes_attribute)


def link_elimination(O, keep_all_streets=True, verbose=False):
    """
    Generating a network fo one-way streets. A greedy algorithm that sequentially removes links from the graph
    until no link can be removed without losing strong connectivity.

    The problem is referred to in the literature as One-Way Traffic Organization problem (OWTOP).

    Parameters
    ----------
    O: nx.DiGraph
        owtop graph, an initial directed graph with links labeled as fixed (direction cannot change) or not fixed
    keep_all_streets : bool
        if false, complete streets can be removed as long as all nodes are strongly connected
    verbose : bool
        print internal details during the process

    Returns
    -------
    O : nx.DiGraph
        a copy of the graph after link elimination
    """

    # Get the giant weakly connected component (remove any unconnected parts)
    gcc = sorted(nx.weakly_connected_components(O), key=len, reverse=True)[0]
    O = O.subgraph(gcc).copy()

    # Add complementary edges
    for i, data in O.edges.items():
        if data.get('fixed', False) == False:
            O.add_edge(i[1], i[0], fixed=False)

    if verbose:
        print('Initialized graph has ', len(O.nodes), ' nodes and ', len(O.edges), ' edges')

    if not nx.is_strongly_connected(O):
        print('Initialized graph is not strongly connected')
        return

    def opposite_direction_exists(O, *edge_id):
        return O.has_edge(edge_id[1], edge_id[0])

    # Remove edges
    i = 0
    while True:
        i+=1
        if verbose:
            print('Iteration ', i)
        # Calculate betweenness centrality
        bc = nx.edge_betweenness_centrality(O)
        nx.set_edge_attributes(O, bc, 'bc')
        edges = [edge for edge in list(O.edges.items()) if edge[1].get('fixed', False) == False]

        # Finish the loop if no edge candidates exist
        if len(edges) == 0:
            break
        edges = sorted(edges, key=lambda x: x[1]['bc'])
        edge = list(edges)[0]
        edge_id = edge[0]

        # Check if the new graph is strongly connected
        H = O.copy()
        H.remove_edge(*edge_id)
        if nx.is_strongly_connected(H) and (opposite_direction_exists(O, *edge_id) or not keep_all_streets):
            O.remove_edge(*edge_id)
        else:
            nx.set_edge_attributes(O, {edge_id: {'fixed': True}})

    return O


def rebuild_lanes_from_owtop_graph(
        G,
        O,
        hierarchies_to_protect=[],
        source_lanes_attribute=constants.KEY_LANES_DESCRIPTION,
        target_lanes_attribute=constants.KEY_LANES_DESCRIPTION_AFTER
):
    """
    Update lanes in the street graph to match the topology in the owtop graph

    Parameters
    ----------
    G : nx.MultiGraph
        street graph
    O : nx.DiGraph
        owtop graph
    hierarchies_to_protect : list
        which street hierarchies should not be changed
    source_lanes_attribute : str
        attribute holding the lanes that should be used as input
    target_lanes_attribute : str
        attribute holding the lanes that should be used as output

    Returns
    -------
    None
    """

    n_car_lanes = {}
    for id, data in G.edges.items():
        u, v, k = id
        n_car_lanes[(u, v)] = O.has_edge(u, v) * 1
        n_car_lanes[(v, u)] = O.has_edge(v, u) * 1

    for id, data in G.edges.items():
        u, v, k = id
        lanes_before = data[source_lanes_attribute]
        lanes_after = lanes_before.copy()

        if data['hierarchy'] not in hierarchies_to_protect:

            for i, l in enumerate(lanes_before):

                # M- lanes
                if l == constants.LANETYPE_MOTORIZED + constants.DIRECTION_BOTH:

                    if n_car_lanes[(u, v)] >= 1 and n_car_lanes[(v, u)] >= 1:
                        # keep the lane as it is
                        n_car_lanes[(u, v)] -= 1
                        n_car_lanes[(v, u)] -= 1

                    elif n_car_lanes[(u, v)] >= 1 and n_car_lanes[(v, u)] == 0:
                        # turn it into [L<,M>]
                        lanes_after[i] = [
                            constants.LANETYPE_CYCLING_LANE + constants.DIRECTION_BACKWARD,
                            constants.LANETYPE_MOTORIZED + constants.DIRECTION_FORWARD,
                        ]
                        n_car_lanes[(u, v)] -= 1

                    elif n_car_lanes[(u, v)] == 0 and n_car_lanes[(v, u)] >= 1:
                        # convert it into [M<,L>]
                        lanes_after[i] = [
                            constants.LANETYPE_MOTORIZED + constants.DIRECTION_BACKWARD,
                            constants.LANETYPE_CYCLING_LANE + constants.DIRECTION_FORWARD,
                        ]
                        n_car_lanes[(v, u)] -= 1

                    else:
                        # convert it into [P<,P>]
                        lanes_after[i] = [
                            constants.LANETYPE_CYCLING_TRACK + constants.DIRECTION_BACKWARD,
                            constants.LANETYPE_CYCLING_TRACK + constants.DIRECTION_FORWARD,
                        ]
                        
                        if constants.LANETYPE_CYCLING_LANE+constants.DIRECTION_BACKWARD in lanes_before:
                            lanes_after[lanes_before.index(constants.LANETYPE_CYCLING_LANE+constants.DIRECTION_BACKWARD)] = constants.LANETYPE_CYCLING_TRACK+constants.DIRECTION_BACKWARD

                        if constants.LANETYPE_CYCLING_LANE+constants.DIRECTION_FORWARD in lanes_before:
                            lanes_after[lanes_before.index(constants.LANETYPE_CYCLING_LANE+constants.DIRECTION_FORWARD)] = constants.LANETYPE_CYCLING_TRACK+constants.DIRECTION_FORWARD


                # M< and M> lanes
                if l in [
                    constants.LANETYPE_MOTORIZED + constants.DIRECTION_BACKWARD,
                    constants.LANETYPE_MOTORIZED + constants.DIRECTION_FORWARD
                ]:

                    if n_car_lanes[(v, u)] >= 1:
                        # convert into M<
                        lanes_after[i] = constants.LANETYPE_MOTORIZED + constants.DIRECTION_BACKWARD
                        n_car_lanes[(v, u)] -= 1

                    elif n_car_lanes[(u, v)] >= 1:
                        # convert into M>
                        lanes_after[i] = constants.LANETYPE_MOTORIZED + constants.DIRECTION_FORWARD
                        n_car_lanes[(u, v)] -= 1

                    else:
                        # convert it into [P<,P>]
                        lanes_after[i] = [
                            constants.LANETYPE_CYCLING_TRACK + constants.DIRECTION_BACKWARD,
                            constants.LANETYPE_CYCLING_TRACK + constants.DIRECTION_FORWARD,
                        ]
                        #check for any L<,L> lanes that are still in lanes_before and convert them to P<,P>
                        if constants.LANETYPE_CYCLING_LANE+constants.DIRECTION_BACKWARD in lanes_before:
                             lanes_after[lanes_before.index(constants.LANETYPE_CYCLING_LANE+constants.DIRECTION_BACKWARD)] = constants.LANETYPE_CYCLING_TRACK+constants.DIRECTION_BACKWARD

                        if constants.LANETYPE_CYCLING_LANE+constants.DIRECTION_FORWARD in lanes_before:
                            lanes_after[lanes_before.index(constants.LANETYPE_CYCLING_LANE+constants.DIRECTION_FORWARD)] = constants.LANETYPE_CYCLING_TRACK+constants.DIRECTION_FORWARD


        data[target_lanes_attribute] = utils.reorder_lanes(list(utils.flatten_list(lanes_after)))
