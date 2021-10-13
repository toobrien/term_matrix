from csv import QUOTE_NONNUMERIC, reader
from dash import callback_context, Dash
import dash_table as dt
from dash_html_components import Div, Td, Tr, Table
from dash_core_components import Dropdown, Graph, Input
from dash.dependencies import Input, Output
from json import loads
import plotly.graph_objects as go
from spread_matrix import idx, spread_row
from time import time

# CONSTANTS

app = Dash(__name__)
app.title = "spread_matrix"

# data
cells = {}
rows = {}

# figure layouts
margins = {
    "l": 10,
    "r": 10
}

scatterplot_layout = {
    "width": 550,
    "height": 400,
    "margin": margins
}

pdf_layout = {
    "width": 400,
    "height": 400,
    "margin": margins
}

heatmap_layout = {
    "width": 400,
    "height": 400,
    "margin": margins
}

table_layout = {
    "width": 1300,
    "height": 400
}

element_references = {
    "table": None,
    "scatterplot": None,
    "pdf": None,
    "heatmap": None
}

step = 0.8 / 25
min_opacity = 0.2 - step

# FUNCTIONS

def get_contract(cell):

    return cell["column_id"][0:2]


def get_spread_rows(cell):

    spread_row_subset = None

    if cell:
        contract = get_contract(cell)
        labels = cells[contract]["labels"]

        front_month = labels[cell["row"]]
        back_month = labels[cell["column"] - 1]
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
            layout = scatterplot_layout
        )

    scatterplot = Graph(
        id = "scatterplot",
        figure = fig
    )

    if spread_rows:

        # build traces: group rows by spread
        traces = {}
        opacity = min_opacity

        for r in spread_rows:

            id = r[spread_row.spread_id]

            if id not in traces:

                color = "#0000FF"
                if r[spread_row.cell_id] == id: color = "#FF0000"
                opacity += step

                traces[id] = {
                    "x": [],
                    "y": [],
                    "text": [],
                    "name": id,
                    "mode": "markers",
                    "marker": {
                        "color": color
                    },
                    "opacity": opacity
                }

            traces[id]["x"].append(r[spread_row.days_listed])
            traces[id]["y"].append(r[spread_row.settle])
            traces[id]["text"].append(r[spread_row.date])

        for id, trace in traces.items():

            fig.add_trace(go.Scatter(**trace))

    return scatterplot


def get_pdf(spread_rows):

    fig = go.Figure(
        layout = pdf_layout
    )

    pdf = Graph(
        id = "pdf",
        figure = fig
    )
    
    if spread_rows:

        fig.add_trace(
            go.Histogram(
                x = [ r[spread_row.settle] for r in spread_rows ],
                histnorm = "probability"
            )
        )

    return pdf


def get_heatmap(contract):

    pct = cells[contract]["percentile"]
    lbls = cells[contract]["labels"]
    
    # reverse so heatmap matches table
    reversed_lbls = lbls[::-1]
    reversed_pct = pct[::-1]

    return Graph(
        id = "heatmap",
        figure = go.Figure(
        layout = heatmap_layout,
        data = go.Heatmap(
                x = lbls,
                y = reversed_lbls,
                z = reversed_pct,
                showscale = False
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
            "height": f"{table_layout['height']}px",
            "overflowY": "auto",
            "overflowX": "auto"
        },
        style_header = {
            "overflow": "hidden"
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
                        style = { 
                            "width": table_layout["width"]
                        },
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
    Output("heatmap_container", "children"),
    Input("contract_dropdown", "value")
)
def update_table_and_heatmap(contract):

    source = callback_context.triggered[0]["prop_id"]

    if source == ".": contract = config["enabled"][0]

    table = get_data_table(contract)
    heatmap = get_heatmap(contract)

    return table, heatmap

@app.callback(
    Output("scatterplot_container", "children"),
    Output("pdf_container", "children"),
    Input("data_table", "active_cell")
)
def update_scatter_and_pdf(cell):

    source = callback_context.triggered[0]["prop_id"]

    if source == ".": cell = None

    spread_rows = get_spread_rows(cell)
    
    scatterplot = get_scatterplot(spread_rows)
    pdf = get_pdf(spread_rows)

    return scatterplot, pdf

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