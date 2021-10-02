from contracts import contracts
from json import dumps, loads
from record import record
from spread_matrix import spread_matrix
from sqlite3 import connect
from time import time

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
  
  cur_date = records[0][record.date]
  cur_set = []

  for r in records:
    if r[record.date] != cur_date:
      record_sets.append(cur_set)

      cur_date = r[record.date]
      cur_set = []

    cur_set.append(r)

  record_sets.append(cur_set)

  return record_sets

def get_spread_matrix(contract, start, end):
  db = get_db()

  name = contracts[contract]["srf_name"]
  records = get_records(db, name, start, end)
  record_sets = get_record_sets(records)

  sm = spread_matrix(contract, record_sets)

  db.close()

  return sm

if __name__ == "__main__":
  with open("./config.json") as fd:
    config = loads(fd.read())
    output_dir = config["output_dir"]

    start = "2005-01-01"
    end = "2035-01-01"

    for contract in [ 
      "ZC", "ZS", "ZM", "ZL", "ZW", "KE",
      "HE", "LE",
      "GE",
      "NG", "CL", "HO", "RB"
    ]:
      t0 = time()
      sm = get_spread_matrix(contract, start, end)
      t1 = time()
      print(f"{contract}: {(t1 - t0):0.2f} s")

      with open(f"{output_dir}{contract}.html", "w") as fd:
        fd.write(sm.table("html").__str__())
      
      with open(f"{output_dir}{contract}.json", "w") as fd:
        fd.write(dumps(sm.get_json()))
