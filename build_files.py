from contracts import contracts
from csv import QUOTE_NONNUMERIC, writer
from json import loads
from record import record
from spread_matrix import idx, headers, spread_matrix
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
      active_contracts = { k : contracts[k] for k in config["enabled"] }

      start = "2000-01-01"
      end = "2035-01-01"

      for contract in active_contracts:

        t0 = time()
        sm = get_spread_matrix(contract, start, end)

        labels = sm.get_labels()

        for i in idx:
          
            with open(f"{output_dir}{contract}_{i}.csv", "w", newline = '') as fd:
                
                cells = sm.get_cells(i)

                w = writer(fd, quoting = QUOTE_NONNUMERIC)
                w.writerow(labels)
                w.writerows(cells)
      
        with open(f"{output_dir}{contract}.csv", "w", newline = '') as fd:
        
            lines = sm.get_rows()
            w = writer(fd, quoting = QUOTE_NONNUMERIC)
            w.writerow(headers)
            w.writerows(lines)

        t1 = time()
        print(f"{contract}: {(t1 - t0):0.2f} s")
