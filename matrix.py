from enum import IntEnum
from json import dumps, loads
from numpy import apply_along_axis, empty, nanmedian, NaN, ndarray, set_printoptions, nanstd
from sqlite3 import connect
from sys import maxsize
from tabulate import tabulate
from time import time

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
  "F", "G", "H", "J", "K", "M"
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
  m = empty((len(record_sets), width * 12, width * 12), dtype="i,i,i,U10")

  d[::] = NaN
  m[::] = NaN

  for i in range(len(record_sets)):
    record_set = record_sets[i]
    base_year = record_set[0][rec.year]

    for j in range(len(record_set)):
      r0 = record_set[j]
      row = 12 * (r0[rec.year] - base_year) + month_atoi[r0[rec.month]]
      
      for k in range(j + 1, len(record_set)):
        r1 = record_set[k]
        col = 12 * (r1[rec.year] - base_year) + month_atoi[r1[rec.month]]
        
        d[i][row][col] = r0[rec.settle] - r1[rec.settle]

        m[i][row][col] = (
          r0[rec.year],
          r1[rec.year],
          r0[rec.days_listed],
          r0[rec.date]
        )
        
  
  return d, m

def table(d, m):
  t_med = apply_along_axis(nanmedian, 0, d)
  t_std = apply_along_axis(nanstd, 0, d)
  
  today = m.shape[0] - 1
  dim = m.shape[1]
  
  t = empty(shape = (dim, dim), dtype = "f,f,f")

  for i in range(dim):
    for j in range(dim):
      t[i, j] = ( 
        d[today, i, j],
        t_med[i, j],
        t_std[i, j]
      )

  return t


if __name__ == "__main__":
    db = get_db()

    name = contracts["ZC"]["name"]
    width = contracts["ZC"]["width"]

    start = time()
    records = get_records(db, name, "2005-01-01", "2035-01-01")
    record_sets = get_record_sets(records)
    end = time()
    print(f"records: {end - start} ms")

    start = time()
    d, m = matrix(record_sets, width)
    end = time()
    print(f"matrix: {end - start} ms")

    start = time()
    t = table(d, m)
    end = time()
    print(f"table: {end - start}")

    #for record in records:
    #  print(record)

    #for record_set in record_sets:
    #  print(dumps(record_set))

    set_printoptions(threshold = maxsize)
    #print(m[len(m) - 1, :, :])
    print(t)