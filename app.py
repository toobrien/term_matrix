from csv import QUOTE_NONNUMERIC, reader
from dash import Dash
import dash_table as dt
from dash_html_components import Div, Td, Tr, Table
from dash_core_components import Dropdown, Graph, Input as CInput
from dash.dependencies import Input, Output, State
from json import loads
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from spread_matrix import idx
from time import time

app = Dash(__name__)

cells = {}
rows = {}

def load_rows(config):

    output_dir = config["output_dir"]

    for contract in config["enabled"]:
            
        with open(f"{output_dir}/{contract}.csv") as fd:
            
            r = reader(fd, quoting = QUOTE_NONNUMERIC)
            rows[contract] = [ row for row in r ]
    
def load_cells(config):

    output_dir = config["output_dir"]
    
    for contract in config["enabled"]:

        cells[contract] = {}

        for i in idx:

            with open(f"{output_dir}/{contract}_{i}.csv") as fd:

                r = reader(fd, quoting = QUOTE_NONNUMERIC)
                data = [ cell_row for cell_row in r ]
                labels = data[0]
                data = data[1:]

                cells[contract][i] = data
                cells[contract]["labels"] = labels

def get_graph_row(config):
    
    graph_row = Tr(
        id = "graph_row",
        children = [
            Table([
                Tr([
                    Td([
                        #Graph(
                        #    id = "scatterplots"
                        #)
                    ]),
                    Td([
                        #Graph(
                        #    id = "pdf"
                        #)
                    ]),
                    Td([
                        Div(
                            id = "statistics",
                            children = []
                        )
                    ])
                ])
            ])
        ]
    )

    return graph_row

def get_matrix_row(config):

    default_contract = config["enabled"][0]
    pct = cells[default_contract]["percentile"]
    lbls = cells[default_contract]["labels"]

    matrix_row = Tr(
        id = "matrix_row",
        children = [
            Div(
                id = "heatmap_container",
                children = [
                    Graph(
                        id = "heatmap",
                        figure = go.Figure(
                            layout = {
                                "width": 600,
                                "height": 600
                            },
                            data = go.Heatmap(
                                x = lbls,
                                y = lbls,
                                z = pct
                            )
                        )
                    )
                ]
            )
        ]
    )

    #    matrix_row = Tr(
    #    id = "matrix_row",
    #    children = [
    #        dt.DataTable(
    #            id = "data_table",
    #            data = df.to_dict("records"),
    #            columns=[ { "name": i, "id": i } for i in df.columns ]
    #        )
    #    ]
    #)

    return matrix_row

def get_select_row(config):

    selections = [ 
        Td(
            id = f"{contract}_select",
            children = [ contract ]
        )
        for contract in config["enabled"]
    ]

    select_row = Tr(
        id = "select_row",
        children = [
            Table([
                Tr(selections)
            ])
        ]
    )

    return select_row

def get_layout(config):

    graph_row = get_graph_row(config)
    matrix_row = get_matrix_row(config)
    select_row = get_select_row(config)

    return Table(
        id = "root",
        children = [
            graph_row,
            matrix_row,
            select_row,
        ]
    )

def update_table():

    pass

def update_chart():

    pass

if __name__ == "__main__":

    with open("./config.json") as fd:

        t0 = time()

        config = loads(fd.read())

        load_rows(config)
        load_cells(config)

        app.layout = get_layout(config)

        t1 = time()
        print(f"view loaded in {(t1 - t0):0.2f} s")

        app.run_server(debug = True)