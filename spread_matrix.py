from contracts import contracts
from enum import IntEnum
from record import record
from numpy import apply_along_axis, empty, isnan, nanmedian, NaN, sort, searchsorted, nanstd, warnings
from record import record
#from sys import maxsize
from tabulate import tabulate

warnings.filterwarnings('ignore')

# CONSTANTS
class meta(IntEnum):
    row_year = 0
    col_year = 1
    days_listed = 2
    date = 3

class spread_row(IntEnum):
    cell_id = 0
    spread_id = 1
    date = 2
    settle = 3
    days_listed = 4

headers = [ "cell_id", "spread_id", "date", "settle", "days_listed" ]
idx = [ "spread", "percentile", "median", "stdev", "days_listed" ]

month_atoi = {
    "F": 0,
    "G": 1,
    "H": 2,
    "J": 3,
    "K": 4,
    "M": 5,
    "N": 6,
    "Q": 7,
    "U": 8,
    "V": 9,
    "X": 10,
    "Z": 11
}

month_itoa = [
    "F", "G", "H", "J", "K", "M",
    "N", "Q", "U", "V", "X", "Z"
]

# UTILITY FUNCTIONS
def matrix(record_sets, width):

    d = empty((len(record_sets), width, width), dtype="f")
    md = empty((len(record_sets), width, width), dtype="i,i,i,U10")

    d.fill(NaN)
    md.fill(NaN)

    for i in range(len(record_sets)):

        record_set = record_sets[i]
        base_year = record_set[0][record.year]

        for j in range(len(record_set)):

            front = record_set[j]
            row = 12 * (front[record.year] - base_year) + month_atoi[front[record.month]]

            if row >= width: break
        
            for k in range(j + 1, len(record_set)):

                back = record_set[k]
                col = 12 * (back[record.year] - base_year) + month_atoi[back[record.month]]

                if col >= width: break
            
                d[i][row][col] = -front[record.settle] + back[record.settle]

                md[i][row][col] = (
                    front[record.year],
                    back[record.year],
                    back[record.days_listed],
                    back[record.date]
                )

    return d, md

def rank(a):

  a_0 = a[~isnan(a)]
  a_1 = sort(a_0)
  todays_spread = a[-1]
  return searchsorted(a_1, todays_spread) / len(a_1)

# CLASS
class spread_matrix:

    def __init__(self, contract, record_sets):

        max_years = contracts[contract]
        
        d, md = matrix(record_sets, max_years * 12)
        
        t_med = apply_along_axis(nanmedian, 0, d)
        t_std = apply_along_axis(nanstd, 0, d)
        t_pct = apply_along_axis(rank, 0, d)

        dim = d.shape[1]
        depth = d.shape[0]
        today = depth - 1
        todays_records = record_sets[today]

        self.cells = { i : [] for i in idx }
        cell_map = {}
        lbls = []

        rows = []

        # set row/col labels, intialize and map cells
        base_year = todays_records[0][record.year]
        width = 0

        for i in range(len(todays_records)):

            r = todays_records[i]
            m = r[record.month]
            y = r[record.year]

            if y - base_year < max_years:

                y_i = r[record.year] % 100
                y_s = str(r[record.year])[2:]

                lbls.append(f"{contract}{m}{y_s}")

                cell_map[(m, y_i)] = i

                width += 1
        
        for i in range(width):

            for i in idx:

                self.cells[i].append([ 0 for i in range(width) ])

        # set cell data, json records
        for i in range(dim):

            if i // 12 >= max_years: break

            for j in range(dim):
            
                if j // 12 >= max_years: break

                spread = d[today, i, j]
                
                if isnan(spread): continue
            
                # statistics
                mdt = md[today, i, j]
                pct = t_pct[i, j]
                med = t_med[i, j]
                std = t_std[i, j]
                dl = mdt[meta.days_listed]

                # indexes
                front_month = month_itoa[i % 12]
                back_month = month_itoa[j % 12]
                
                front_year = mdt[meta.row_year] % 100
                back_year = mdt[meta.col_year] % 100

                row = cell_map[(front_month, front_year)]
                col = cell_map[(back_month, back_year)]
                
                self.cells["spread"][row][col] = spread
                self.cells["percentile"][row][col] = round(pct, 3)
                self.cells["median"][row][col] = med
                self.cells["stdev"][row][col] = round(std, 2)
                self.cells["days_listed"][row][col] = dl

                # scatterplot, histogram, etc. data
                cell_id = f"{front_month}{front_year}/{back_month}{back_year}"

                for k in range(depth):
                    
                    settle = d[k, i, j]
                    
                    if ~isnan(settle):

                        mdk = md[k, i, j]
                        front_year_k = str(mdk[meta.row_year])[2:]
                        back_year_k = str(md[k, i, j][meta.col_year])[2:]
                        spread_id_k = f"{front_month}{front_year_k}/{back_month}{back_year_k}"                        
                        date_k = mdk[meta.date]
                        days_listed_k = int(mdk[meta.days_listed])

                        rows.append(
                            [ 
                                cell_id,
                                spread_id_k,
                                date_k,
                                settle,
                                days_listed_k,
                            ]
                        )
        self.set_rows(rows)
        self.set_labels(lbls)
        self.set_metadata(md)
        self.set_data(d)
        
    def table(self, fmt):

        return tabulate(self.get_cells(), self.get_labels(), fmt)

    def set_cells(self, cells): self.cells = cells
    def set_data(self, data): self.data = data
    def set_labels(self, labels): self.labels = labels
    def set_metadata(self, metadata): self.metadata = metadata
    def set_rows(self, rows): self.rows = rows

    def get_cells(self, i): return self.cells[i]
    def get_data(self): return self.data
    def get_labels(self): return self.labels
    def get_metadata(self): return self.metadata
    def get_rows(self): return self.rows
