from enum import IntEnum
from json import dumps, loads
from numpy import apply_along_axis, empty, isnan, nanmedian, NaN, ndarray, sort, searchsorted, set_printoptions, nanstd, warnings
from sqlite3 import connect
from sys import maxsize
from tabulate import tabulate
from time import time

warnings.filterwarnings('ignore')

class rec(IntEnum):
  name = 0
  month = 1
  year = 2
  date = 3
  settle = 4
  days_listed = 5

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

contracts = {
  "ZC":  { "name": "C", "width": 5 },
  "ZS": { "name": "S", "width": 4 },
  "GE": { "name": "ED", "width": 10 }
}

def get_db():
  db = None

  with open("./config.json") as fd:
    db_path = loads(fd.read())["db"]
    db = connect(db_path)  

  return db

def get_records(db, name, begin, end):
  cur = db.cursor()

  records = cur.execute(f'''
            SELECT DISTINCT
                name,
                month,
                CAST(year as INT),
                date,
                settle,
                CAST(julianday(date) - julianday(from_date) AS INT)
            FROM ohlc INNER JOIN metadata USING(contract_id)
            WHERE name = "{name}"
            AND date BETWEEN "{begin}" AND "{end}"
            ORDER BY date ASC, year ASC, month ASC;
        ''').fetchall()

  return records

def get_record_sets(records):
  record_sets = []
  
  cur_date = records[0][rec.date]
  cur_set = []

  for record in records:
    if record[rec.date] != cur_date:
      record_sets.append(cur_set)

      cur_date = record[rec.date]
      cur_set = []

    cur_set.append(record)

  record_sets.append(cur_set)

  return record_sets

def matrix(record_sets, width):
  d = empty((len(record_sets), width * 12, width * 12), dtype="f")
  md = empty((len(record_sets), width * 12, width * 12), dtype="i,i,i,U10")

  d[::] = NaN
  md[::] = NaN

  for i in range(len(record_sets)):
    record_set = record_sets[i]
    base_year = record_set[0][rec.year]

    for j in range(len(record_set)):
      front = record_set[j]
      row = 12 * (front[rec.year] - base_year) + month_atoi[front[rec.month]]
      
      for k in range(j + 1, len(record_set)):
        back = record_set[k]
        col = 12 * (back[rec.year] - base_year) + month_atoi[back[rec.month]]
        
        d[i][row][col] = front[rec.settle] - back[rec.settle]

        md[i][row][col] = (
          front[rec.year],
          back[rec.year],
          back[rec.days_listed],
          back[rec.date]
        )

  return d, md

def rank(a):
  a_0 = a[~isnan(a)]
  a_1 = sort(a_0)
  return searchsorted(a_1, a[0]) / len(a)

if __name__ == "__main__":
  db = get_db()

  name = contracts["ZC"]["name"]
  width = contracts["ZC"]["width"]

  start = time()
  records = get_records(db, name, "2005-01-01", "2035-01-01")
  record_sets = get_record_sets(records)
  end = time()
  print(f"records: {end - start:0.2f} s")

  start = time()
  d, md = matrix(record_sets, width)
  end = time()
  print(f"matrix: {end - start:0.2f} s")

  start = time()
  t_med = apply_along_axis(nanmedian, 0, d)
  t_std = apply_along_axis(nanstd, 0, d)
  t_pct = apply_along_axis(rank, 0, d)
  end = time()
  print(f"table: {end - start:0.2f} s\n")

  #for record in records:
  #  print(record)

  #for record_set in record_sets:
  #  print(dumps(record_set))

  #set_printoptions(threshold = maxsize)
  #print(m[m.shape[0] - 1, :, :])
  #print(d[d.shape[0] - 1, :, :])
  #print(t_med)
  #print(t_std)
  #print(t_pct)

  dim = d.shape[1]
  today = md.shape[0] - 1
  total = 0

  for i in range(dim):
    for j in range(dim):
      spread = d[today, i, j]

      if ~isnan(spread):
        mdt = md[today, i, j]

        pct = t_pct[i, j]
        med = t_med[i, j]
        std = t_std[i, j]

        front_month = month_itoa[i % 12]
        back_month = month_itoa[j % 12]
        
        front_year = mdt[meta.row_year] % 100
        back_year = mdt[meta.col_year] % 100
        
        dl = mdt[meta.days_listed]

        print(f"front  : ZC{front_month}{front_year}")
        print(f"back   : ZC{back_month}{back_year}")
        print(f"dl     : {dl}")

        print(f"spread : {spread}")
        print(f"pct    : {pct:0.3f}")
        print(f"med    : {med}")
        print(f"std    : {std:0.3f}\n")

        total += 1
  
  print(f"total: {total}")

  