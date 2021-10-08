from csv import QUOTE_NONNUMERIC, reader
from dash import callback_context, Dash
import dash_table as dt
from dash_html_components import Div, Td, Tr, Table
from dash_core_components import Dropdown, Graph, Input as CInput
from dash.dependencies import Input, Output, State
from json import dumps, loads
import plotly.graph_objects as go
from spread_matrix import idx, spread_row
from time import time


app = Dash(__name__)

cells = {}
rows = {}

default_layout = {
    "width": 500,
    "height": 400
}

element_references = {
    "table": None,
    "scatterplot": None,
    "pdf": None,
    "heatmap": None
}

def get_contract(cell):

    return cell["column_id"][0:2]


def get_spread_rows(cell):

    spread_row_subset = None

    if cell:
        contract = get_contract(cell)
        labels = cells[contract]["labels"]

        front_month = labels[cell["row"]]
        back_month = labels[cell["column"]]
        cell_id = f"{front_month[2:]}/{back_month[2:]}"

        spread_row_set = rows[contract]

        spread_row_subset = [ 
                        row for row in spread_row_set 
                        if row[spread_row.cell_id] == cell_id
                    ]
    
    return spread_row_subset


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


def get_scatterplot(spread_rows):

    fig = go.Figure(
            layout = default_layout
        )

    scatterplot = Graph(
        id = "scatterplot",
        figure = fig
    )

    if spread_rows:

        traces = {}

        # build traces: group rows by spread
        for r in spread_rows:

            id = r[spread_row.spread_id]

            if id not in traces:

                traces[id] = {
                    "x": [],
                    "y": [],
                    "name": id
                }

            traces[id]["x"].append(r[spread_row.days_listed])
            traces[id]["y"].append(r[spread_row.settle])

        for id, trace in traces.items():

            fig.add_trace(go.Scatter(**trace))

    return scatterplot


def get_pdf(spread_rows):

    fig = go.Figure(
        layout = default_layout
    )

    pdf = Graph(
        id = "pdf",
        figure = fig
    )
    
    if spread_rows:

        pass

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
                        get_scatterplot(None)
                    ]
                )
            ]),
            Td([
                Div(
                    id = "pdf_container",
                    children = [
                        get_pdf(None)
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
        cell = None

    if source in [ ".", "contract_dropdown.value" ]:

        element_references["table"] = get_data_table(contract)
        element_references["heatmap"] = get_heatmap(contract)

    if source in [ ".", "data_table.active_cell" ]:

        spread_rows = get_spread_rows(cell)
        element_references["scatterplot"] = get_scatterplot(spread_rows)
        element_references["pdf"] = get_pdf(spread_rows)

    return \
        element_references["table"],\
        element_references["scatterplot"],\
        element_references["pdf"],\
        element_references["heatmap"]


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

        #cell = {'row': 0, 'column': 3, 'column_id': 'ZSH22'}
        #spread_rows = get_spread_rows(cell)
        #x = get_scatterplot(spread_rows)

        app.run_server(debug = True)