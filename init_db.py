import sqlite3

connection = sqlite3.connect('database.db')

with open('schema.sql') as f:
  connection.executescript(f.read())
	
cur = connection.cursor()

cur.execute("INSERT INTO packages (name, version, dependencies) VALUES (?,?,?)",
  ('sample',"1.0","sample2")
  )

cur.execute("INSERT INTO packages (name, version, dependencies) VALUES (?,?,?)",
  ('sample2',"1.1","other,other2")
)
	
connection.commit()
connection.close()
	
