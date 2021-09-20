from json import loads
from numpy import ndarray
from sqlite3 import connect

months = {
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

contracts = {
  "ZC":  { "name": "C", "width": 4 },
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
                year,
                date,
                settle,
                julianday(date) - julianday(from_date) AS days_listed
            FROM ohlc INNER JOIN metadata USING(contract_id)
            WHERE name = "{name}"
            AND date BETWEEN "{begin}" AND "{end}"
            ORDER BY date ASC, year ASC, month ASC;
        ''').fetchall()

  return records

def matrix(records, width):
  return None

if __name__ == "__main__":

    db = get_db()

    name = contracts["ZC"]["name"]
    width = contracts["ZC"]["width"]
    
    records = get_records(db, name, "2005-01-01", "2035-01-01")
    m = matrix(records, width)

    for record in records:
      print(record)
