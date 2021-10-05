from csv import QUOTE_NONNUMERIC, reader
from dash import callback_context, Dash
import dash_table as dt
from dash_html_components import Div, Td, Tr, Table
from dash_core_components import Dropdown, Graph, Input as CInput
from dash.dependencies import Input, Output, State
from json import dumps, loads
import plotly.graph_objects as go
from spread_matrix import idx
from time import time


app = Dash(__name__)

cells = {}
rows = {}

default_layout = {
    "width": 500,
    "height": 400
}

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


def get_scatterplot(contract, cell):

    scatterplot = None

    if cell:
        pass
    else:
        scatterplot = Graph(
            id = "scatterplot",
            figure = go.Figure(
                layout = default_layout
            )
        )

    return scatterplot


def get_pdf(contract, cell):

    pdf = None
    
    if cell:
        pass
    else:
        pdf = Graph(
            id = "pdf",
            figure = go.Figure(
                layout = default_layout
            )
        )
    
    return pdf


def get_heatmap(contract):

    pct = cells[contract]["percentile"]
    lbls = cells[contract]["labels"]
    
    return Graph(
        id = "heatmap",
        figure = go.Figure(
        layout = default_layout,
        data = go.Heatmap(
                x = lbls,
                y = lbls,
                z = pct,
                transpose = True
            )
        )
    )


def get_graph_row(config):
    
    default_contract = config["enabled"][0]

    graph_row = Tr(
        id = "graph_row",
        children = [
            Td([
                Div(
                    id = "scatterplot_container",
                    children = [
                        get_scatterplot(None, None)
                    ]
                )
            ]),
            Td([
                Div(
                    id = "pdf_container",
                    children = [
                        get_pdf(None, None)
                    ]
                )
            ]),
            Td([
                Div(
                    id = "heatmap_container",
                    children = [
                        get_heatmap(default_contract)
                    ]
                )
            ])
        ]
    )

    return graph_row


def get_data_table(contract):

    pct = cells[contract]["percentile"]
    lbls = cells[contract]["labels"]

    cols =  [ { "name": "", "id": "" } ] +\
            [ { "name": lbl, "id": lbl } for lbl in lbls ]
    
    rows = [ { lbls[i] : row[i] for i in range(len(row)) } for row in pct ]
    for i in range(len(rows)):
        rows[i][""] = lbls[i]
    
    return dt.DataTable(
        id = "data_table",
        columns = cols,
        data = rows,
        fixed_rows = { "headers": True },
        style_table = { 
            "height": f"{default_layout['height']}px",
            "overflowY": "auto"
        }
    )


def get_matrix_row(config):

    default_contract = config["enabled"][0]
    
    matrix_row = Tr(
        id = "matrix_row",
        children = [
            Td(
                colSpan = 3,
                children = [
                    Div(
                        id = "data_table_container",
                        children = [ 
                            get_data_table(default_contract)
                        ]
                    )
                ]
            )
        ]
    )

    return matrix_row


def get_select_row(config):

    select_row = Tr(
        id = "select_row",
        children = [
            Td([
                Dropdown(
                    id = "contract_dropdown",
                    options = [ 
                        { "label": contract, "value": contract }
                        for contract in config["enabled"]
                    ]
                )
            ]),
            Td([
                # empty
            ]),
            Td([
                # empty
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


@app.callback(
    Output("data_table_container", "children"),
    Output("scatterplot_container", "children"),
    Output("pdf_container", "children"),
    Output("heatmap_container", "children"),
    Input("contract_dropdown", "value"),
    Input("data_table", "active_cell")
)
def update_layout(contract, cell):

    #print(f"triggered: {callback_context.triggered}")
    #print(f"contract: {contract}")
    #print(f"cell: {cell}")

    source = callback_context.triggered[0]["prop_id"]

    if source == ".":
        contract = config["enabled"][0]

    table = get_data_table(contract)
    heatmap = get_heatmap(contract)

    if source == "contract_dropdown.value":

        contract = None
        cell = None

    scatterplot = get_scatterplot(contract, cell)
    pdf = get_pdf(contract, cell)

    return table, scatterplot, pdf, heatmap


if __name__ == "__main__":

    with open("./config.json") as fd:

        t0 = time()
        print("loading...")

        config = loads(fd.read())

        load_rows(config)
        load_cells(config)

        app.layout = get_layout(config)

        t1 = time()
        print(f"complete: {(t1 - t0):0.2f} s")

        app.run_server(debug = True)