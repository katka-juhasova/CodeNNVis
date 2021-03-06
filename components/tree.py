import logging
import json
import urllib
from igraph import Graph
import plotly.graph_objects as go
from constant import DIAGRAM_COLORS as COLORS
import dash_core_components as dcc


log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
log.addHandler(logging.StreamHandler())


class Tree:
    """
    Class for visualization of the AST structure of the source code.

    Attributes
    ----------
    data : dict
        pre-processed data read from the JSON file
    edges : list
        list of edges of the AST
    colors : list
        list of colors as they are assigned to each node of the tree, colors
        are assigned according to the type of statement that the nodes
        represent (require, variable, function, interface, other)
    text : list
        list of the texts (parts of the source code) which are contained within
        the nodes

    Methods
    -------
    get_figure(horizontal=False)
        Returns go.Figure instance containing the tree diagram representing
        the AST of the source code.
    view(dash_id, horizontal=False, height=None)
        Returns dcc.Graph instance containing the tree diagram representing
        the AST of the source code.
    """

    def __init__(self, path=None, url=None, data=None):
        """
        According to the parameters given, the preprocessed data are read
        from JSON file (parameter path) or from the given url or
        simply copied from the given parameter data. If none of
        the parameters is provided, the function raises an error. Furthermore,
        other attributes are initialized.

        Parameters
        ----------
        path : str or None, optional
            path to the JSON file, which contains preprocessed LUA source code
            (default is None)
        url : str or None, optional
            url of the JSON file, which contains preprocessed LUA source code
            (default is None)
        data : dict or None, optional
            preprocessed data already read from JSON file
        """

        if data:
            self.data = data
        else:
            if all(arg is None for arg in {path, url}):
                raise ValueError('Expected either path or url argument')

            if path:
                with open(path) as f:
                    self.data = json.load(f)
            else:
                log.debug('Loading data file from {}'.format(url))
                with urllib.request.urlopen(url) as url_data:
                    self.data = json.loads(url_data.read().decode())

        # all edges between nodes
        self.edges = list()
        # color for each node
        self.colors = ([COLORS['plot-line']]
                       + ['' for _ in range(self.data['nodes_count'])])
        # text for each node
        self.text = ['root'] + ['' for _ in range(self.data['nodes_count'])]

    def __add_child_edges(self, node: dict):
        """
        Builds attributes edges, colors and text so that the tree diagram can
        be created later.

        Parameters
        ----------
        node : dict
            node read from the JSON file containing all the properties such as
            container type, children etc.
        """

        for child in node['children']:
            self.edges.append((node['master_index'], child['master_index']))
            self.colors[child['master_index']] = COLORS[child['container']]
            self.text[child['master_index']] = '({}, {})'.format(
                child['master_index'], child['container'])

            if 'children' in child:
                self.__add_child_edges(child)

    def get_figure(self, horizontal=False) -> go.Figure:
        """
        Returns a figure containing tree diagram representing the AST of
        the source code.

        Parameters
        ----------
        horizontal : bool, optional
            determines, whether the tree should be oriented horizontally or
            vertically (default is False)

        Returns
        -------
        go.Figure
            go.Figure instance containing the tree diagram representing
            the AST of the source code
        """

        # nodes from .json plus root node
        nodes_count = self.data['nodes_count'] + 1

        # edges from root to the nodes of depth 1
        for node in self.data['nodes']:
            self.edges.append((0, node['master_index']))
            self.colors[node['master_index']] = COLORS[node['container']]
            self.text[node['master_index']] = '({}, {})'.format(
                node['master_index'], node['container'])

            # all other edges to child nodes
            if 'children' in node:
                self.__add_child_edges(node)

        graph = Graph(n=self.data['nodes_count'] + 1, directed=True)
        graph.add_edges(self.edges)

        # build layout with Reingold-Tilford algorithm
        layout = graph.layout_reingold_tilford(mode='out', root=[0])
        # node positions in graph
        positions = {k: layout[k] for k in range(nodes_count)}
        max_y = max([layout[k][1] for k in range(nodes_count)])

        # count node and edge positions and switch original x and y
        # coordinates so that tree would branch horizontally
        nodes_x = [2 * max_y - positions[k][1] for k in range(len(positions))]
        nodes_y = [positions[k][0] for k in range(len(positions))]
        edges_x = list()
        edges_y = list()

        for edge in self.edges:
            edges_y += [positions[edge[0]][0], positions[edge[1]][0], None]
            edges_x += [2 * max_y - positions[edge[0]][1],
                        2 * max_y - positions[edge[1]][1], None]

        if horizontal:
            # just swap axis x and y for horizontal display of the tree
            nodes_x = [x for x in nodes_x]
            nodes_y = [y for y in nodes_y]
            nodes_x, nodes_y = nodes_y, nodes_x
            edges_x, edges_y = edges_y, edges_x

        else:
            # mirror the graph in both directions so that the edges
            # are oriented form left to right and nodes in order from
            # the smallest to the largest
            nodes_x = [-x for x in nodes_x]
            nodes_y = [-y for y in nodes_y]
            edges_x = list(map(lambda x: -x if x else x, edges_x))
            edges_y = list(map(lambda y: -y if y else y, edges_y))

        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                x=edges_x,
                y=edges_y,
                mode='lines',
                line={
                    'width': 1,
                    'color': COLORS['plot-line']
                },
                hoverinfo='none'
            )
        )

        fig.add_trace(
            go.Scatter(
                x=nodes_x,
                y=nodes_y,
                mode='markers',
                marker={
                    'size': 10,
                    'color': self.colors,
                    'line': {
                        'width': 0.5,
                        'color': 'white'
                    }
                },
                text=self.text,
                hoverinfo='text',
                opacity=0.8
            )
        )

        # hide axis line, grid, tick labels and title
        axis = dict(showline=False,
                    zeroline=False,
                    showgrid=False,
                    showticklabels=False,
                    )

        if horizontal:
            fig.update_layout(
                template='plotly_white',
                xaxis=axis,
                yaxis=axis,
                showlegend=False,
                margin={'l': 40, 'r': 40, 'b': 10, 't': 0}
            )
        else:
            fig.update_layout(
                template='plotly_white',
                height=650,
                xaxis=axis,
                yaxis=axis,
                showlegend=False,
                margin={'l': 10, 'r': 10, 'b': 0, 't': 0}
            )

        return fig

    def view(self, dash_id: str, horizontal=False, height=None):
        """
        Returns dcc.Graph object containing the tree diagram representing the
        AST of the source code. It's optional to set the height of diagram
        in pixels.

        Parameters
        ----------
        dash_id : str
            id of the dcc.Graph component
        horizontal : bool, optional
            determines, whether the tree should be oriented horizontally or
            vertically (default is False)
        height : int or None
            height of the diagram (default is None)

        Returns
        -------
        dcc.Graph
            dcc.Graph instance containing the tree diagram representing the
            AST of the source code
        """

        return dcc.Graph(
            id=dash_id,
            figure=self.get_figure(horizontal),
            style={
                'height': height or '250px'
            }
        )
