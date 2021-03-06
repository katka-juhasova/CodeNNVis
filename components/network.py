import logging
from sample import Sample
from plotly.subplots import make_subplots
import plotly.graph_objects as go
from constant import RED_TO_BLUE
import dash_core_components as dcc

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
log.addHandler(logging.StreamHandler())

MARGIN_TOP = 10
MARGIN_LEFT = 50
MARGIN_RIGHT = 50
MARGIN_BOTTOM = 10
CELL_SIZE = 4
ARROW_SIZE = 6
# max is 430, the layers are split in half
MAX_Y = 215
MIDDLE_Y = 107
INPUT_WIDTH = 3
LSTM1_WIDTH = 128
LSTM2_WIDTH = 3
# change these 2 numbers in case of different output layer
OUTPUT_WIDTH = 3
# 40 is space for arrows
LAYERS_LAYOUT_WIDTH = (4 * INPUT_WIDTH + 2 * LSTM1_WIDTH
                       + LSTM2_WIDTH + OUTPUT_WIDTH + 40)


class Network:
    """
    Class for visualization of activations on the layers of the neural
    network. Colors shades (from red to blue) are assigned to the activations
    according to their values. The final visualization consists of 5 distinct
    heatmaps (one for each layer).

    Attributes
    ----------
    sample : Sample
        Sample instance containing everything needed for visualization of
        the activations

    Methods
    -------
    get_figure()
        Returns go.Figure instance containing the visualization of
        the activations on the layers of the neural network.
    view(dash_id)
        Returns dcc.Graph instance containing the visualization of
        the activations on the layers of the neural network.
    """

    def __init__(self, sample: Sample):
        """
        Copies content of parameter sample to the attribute sample.

        Parameters
        ----------
        sample : Sample
            contains everything needed for visualization of sample including
            the information about activations on the layers
        """

        self.sample = sample

    def get_figure(self):
        """
        Creates and returns the figure containing the visualization of
        the activations on the layers of the neural network.

        Returns
        -------
        go.Figure
            go.Figure instance containing the visualization of
            the activations on the layers of the neural network
        """

        # all layers and arrows are subplots in one large figure
        fig = make_subplots(
            rows=1,
            cols=12,
            column_widths=[
                INPUT_WIDTH / LAYERS_LAYOUT_WIDTH,
                INPUT_WIDTH / LAYERS_LAYOUT_WIDTH,
                ARROW_SIZE / LAYERS_LAYOUT_WIDTH,
                INPUT_WIDTH / LAYERS_LAYOUT_WIDTH,
                INPUT_WIDTH / LAYERS_LAYOUT_WIDTH,
                ARROW_SIZE / LAYERS_LAYOUT_WIDTH,
                LSTM1_WIDTH / LAYERS_LAYOUT_WIDTH,
                LSTM1_WIDTH / LAYERS_LAYOUT_WIDTH,
                ARROW_SIZE / LAYERS_LAYOUT_WIDTH,
                LSTM2_WIDTH / LAYERS_LAYOUT_WIDTH,
                ARROW_SIZE / LAYERS_LAYOUT_WIDTH,
                OUTPUT_WIDTH / LAYERS_LAYOUT_WIDTH
            ],
            horizontal_spacing=0.01,
            shared_yaxes=True
        )

        arrow_fig = go.Scatter(
                x=[4, 10, 4, 4],
                y=[102, 107, 112, 102],
                mode='lines',
                line={
                    'color': 'grey',
                    'width': 1
                },
                hoverinfo='none',
                fill='toself',
                showlegend=False
            )

        col = 1
        for layer in self.sample.activations:
            # handle 1D layer
            current_layer = self.sample.activations[layer][0].tolist()
            shape = self.sample.activations[layer].shape

            if len(shape) < 3:

                activations = [0 for _ in range(MAX_Y)]
                y = [i for i in range(MAX_Y)]
                x = [0 for _ in range(MAX_Y)]
                text = [None for _ in range(MAX_Y)]
                current_layer.reverse()

                index = 11 if layer == 3 else 92
                for i, activation in enumerate(current_layer):
                    activations[index] = activation
                    activations[index + 1] = activation
                    activations[index + 2] = activation
                    text[index] = 'y: {}<br>value: {}'.format(
                        len(current_layer) - 1 - i, activation)
                    text[index + 1] = 'y: {}<br>value: {}'.format(
                        len(current_layer) - 1 - i, activation)
                    text[index + 2] = 'y: {}<br>value: {}'.format(
                        len(current_layer) - 1 - i, activation)
                    index += 3

                fig.add_trace(
                    go.Heatmap(
                        z=activations,
                        x=x,
                        y=y,
                        zmin=-1,
                        zmax=1,
                        hovertext=text,
                        showscale=False,
                        hoverinfo='text',
                        colorscale=RED_TO_BLUE
                    ),
                    row=1,
                    col=col
                )
                col += 1

            else:
                # split large 2D layers
                first_half = current_layer[:MAX_Y]
                second_half = current_layer[MAX_Y:]

                # since we want y = 0 at the top af the heat map, original
                # layer needs to be reversed
                reversed_first_half = [
                    first_half[i]
                    for i in range(len(first_half) - 1, -1, -1)
                ]

                reversed_second_half = [
                    second_half[i]
                    for i in range(len(second_half) - 1, -1, -1)
                ]

                x = [i for i in range(len(first_half[0]))]
                y = [i for i in range(len(first_half))]

                text_first_half = [
                    [None for _ in range(len(reversed_first_half[0]))]
                    for _ in range(len(reversed_first_half))]

                for i in range(len(reversed_first_half)):
                    for j in range(len(reversed_first_half[0])):
                        text_first_half[i][j] = (
                            'x: {}<br>y: {}<br>value: {}'.format(
                                j, MAX_Y - i - 1,
                                round(reversed_first_half[i][j], 5)
                            )
                        )

                text_second_half = [
                    [None for _ in range(len(reversed_second_half[0]))]
                    for _ in range(len(reversed_second_half))]

                for i in range(len(reversed_second_half)):
                    for j in range(len(reversed_second_half[0])):
                        text_second_half[i][j] = (
                            'x: {}<br>y: {}<br>value: {}'.format(
                                j, 2 * MAX_Y - i - 1,
                                round(reversed_second_half[i][j], 5)
                            )
                        )

                fig.add_trace(
                    go.Heatmap(
                        z=reversed_first_half,
                        x=x,
                        y=y,
                        hovertext=text_first_half,
                        zmin=-2 if len(x) == INPUT_WIDTH else -1,
                        zmax=2 if len(x) == INPUT_WIDTH else 1,
                        showscale=False,
                        hoverinfo='text',
                        colorscale=RED_TO_BLUE,
                    ),
                    row=1,
                    col=col
                )
                col += 1

                fig.add_trace(
                    go.Heatmap(
                        z=reversed_second_half,
                        x=x,
                        y=y,
                        hovertext=text_second_half,
                        zmin=-2 if len(x) == INPUT_WIDTH else -1,
                        zmax=2 if len(x) == INPUT_WIDTH else 1,
                        showscale=False,
                        hoverinfo='text',
                        colorscale=RED_TO_BLUE,
                    ),
                    row=1,
                    col=col
                )

                col += 1

            # insert arrow
            if layer != len(self.sample.activations) - 1:
                fig.add_trace(
                    arrow_fig,
                    row=1,
                    col=col
                )
                col += 1

        axis_settings = {'showticklabels': False, 'showline': False,
                         'showgrid': False, 'zeroline': False}

        fig.update_layout(
            template='plotly_white',
            width=(MARGIN_RIGHT + MARGIN_LEFT
                   + CELL_SIZE * LAYERS_LAYOUT_WIDTH
                   + 4 * CELL_SIZE * ARROW_SIZE),
            height=MARGIN_TOP + MARGIN_BOTTOM + CELL_SIZE * MAX_Y,
            xaxis=axis_settings,
            yaxis=axis_settings,
            xaxis2=axis_settings,
            yaxis2=axis_settings,
            xaxis3=axis_settings,
            yaxis3=axis_settings,
            xaxis4=axis_settings,
            yaxis4=axis_settings,
            xaxis5=axis_settings,
            yaxis5=axis_settings,
            xaxis6=axis_settings,
            yaxis6=axis_settings,
            xaxis7=axis_settings,
            yaxis7=axis_settings,
            xaxis8=axis_settings,
            yaxis8=axis_settings,
            xaxis9=axis_settings,
            yaxis9=axis_settings,
            xaxis10=axis_settings,
            yaxis10=axis_settings,
            xaxis11=axis_settings,
            yaxis11=axis_settings,
            xaxis12=axis_settings,
            yaxis12=axis_settings,
            margin={'l': MARGIN_LEFT, 'r': MARGIN_RIGHT,
                    't': MARGIN_TOP, 'b': MARGIN_BOTTOM}
        )

        return fig

    def view(self, dash_id: str):
        """
        Creates and returns dcc.Graph object which contains the visualization
        of the activations on the layers of the neural network.

        Parameters
        ----------
        dash_id : str
            id of the dcc.Graph component

        Returns
        -------
        dcc.Graph
            dcc.Graph instance containing the visualization of
            the activations on the layers of the neural network
        """

        return dcc.Graph(
            id=dash_id,
            config={
                'displayModeBar': False
            },
            figure=self.get_figure()
        )
