from contracts import contracts
from enum import IntEnum
from record import record
from numpy import apply_along_axis, empty, isnan, nanmedian, NaN, ndarray, sort, searchsorted, set_printoptions, nanstd, warnings
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
  d = empty((len(record_sets), width * 12, width * 12), dtype="f")
  md = empty((len(record_sets), width * 12, width * 12), dtype="i,i,i,U10")

  d[::] = NaN
  md[::] = NaN

  for i in range(len(record_sets)):
    record_set = record_sets[i]
    base_year = record_set[0][record.year]

    for j in range(len(record_set)):
      front = record_set[j]
      row = 12 * (front[record.year] - base_year) + month_atoi[front[record.month]]
      
      for k in range(j + 1, len(record_set)):
        back = record_set[k]
        col = 12 * (back[record.year] - base_year) + month_atoi[back[record.month]]
        
        d[i][row][col] = front[record.settle] - back[record.settle]

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
    dim = contracts[contract]["width"]
    d, md = matrix(record_sets, dim)
    
    t_med = apply_along_axis(nanmedian, 0, d)
    t_std = apply_along_axis(nanstd, 0, d)
    t_pct = apply_along_axis(rank, 0, d)

    dim = d.shape[1]
    today = md.shape[0] - 1
    total = 0

    cells = []
    cell_map = {}
    lbls = []

    # set row/col labels, map cells
    contract_count = len(record_sets[today])

    for i in range(contract_count):
      r = record_sets[today][i]
      m = r[record.month]
      y = r[record.year] % 100

      lbl = f"{contract}{m}{y}"
      lbls.append(lbl)

      cell_map[(m, y)] = i

      cells.append([ "" for i in range(contract_count) ])

    # set cell data
    for i in range(dim):
      for j in range(dim):
        spread = d[today, i, j]

        if ~isnan(spread):
          mdt = md[today, i, j]

          pct = t_pct[i, j]
          med = t_med[i, j]
          std = t_std[i, j]
          dl = mdt[meta.days_listed]

          front_month = month_itoa[i % 12]
          back_month = month_itoa[j % 12]
          
          front_year = mdt[meta.row_year] % 100
          back_year = mdt[meta.col_year] % 100

          #cell_txt = f"{spread:0.2f}, {pct:0.3f}, ({med}, {std:0.3f})"
          cell_txt = f"{pct:0.3f}"

          row = cell_map[(front_month, front_year)]
          col = cell_map[(back_month, back_year)]
          cells[row][col] = cell_txt

          #print(f"front  : ZC{front_month}{front_year}")
          #print(f"back   : ZC{back_month}{back_year}")
          #print(f"dl     : {dl}")

          #print(f"spread : {spread}")
          #print(f"pct    : {pct:0.3f}")
          #print(f"med    : {med}")
          #print(f"std    : {std:0.3f}\n")

          total += 1

    # label rows
    for i in range(contract_count):
      cells[i].insert(0, lbls[i])

    self.set_cells(cells)
    self.set_labels(lbls)

    self.set_metadata(md)
    self.set_data(d)

    self.set_percentile(t_pct)
    self.set_median(t_med)
    self.set_stdev(t_std)
    self.set_days_listed(dl)
    
    #print(f"total: {total}")

  def table(self, fmt):
    return tabulate(self.get_cells(), self.get_labels(), fmt)

  def set_cells(self, cells): self.cells = cells
  def set_data(self, data): self.data = data
  def set_days_listed(self, days_listed): self.days_listed = days_listed
  def set_labels(self, labels): self.labels = labels
  def set_median(self, median): self.median = median
  def set_metadata(self, metadata): self.metadata = metadata
  def set_percentile(self, percentile): self.percentile = percentile
  def set_stdev(self, stdev): self.stdev = stdev

  def get_cells(self): return self.cells
  def get_data(self): return self.data
  def get_days_listed(self, days_listed): self.days_listed = days_listed
  def get_labels(self): return self.labels
  def get_median(self): return self.median
  def get_metadata(self): return self.metadata
  def get_percentile(self): return self.percentile
  def get_stdev(self): return self.stdev