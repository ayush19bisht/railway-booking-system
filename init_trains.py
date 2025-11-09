import sqlite3

conn = sqlite3.connect('railway.db')
c = conn.cursor()

# Create the trains table
c.execute('''
CREATE TABLE IF NOT EXISTS trains (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    source TEXT NOT NULL,
    destination TEXT NOT NULL,
    seats INTEGER NOT NULL,
    fare REAL NOT NULL
)
''')

conn.commit()
conn.close()
print("✅ Trains table created successfully!")
