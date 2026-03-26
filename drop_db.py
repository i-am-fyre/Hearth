import psycopg2

conn = psycopg2.connect("postgresql://openbudget:postgres@localhost:5433/openbudget")
conn.autocommit = True
cur = conn.cursor()
cur.execute("DROP SCHEMA public CASCADE; CREATE SCHEMA public; GRANT ALL ON SCHEMA public TO public; GRANT ALL ON SCHEMA public TO openbudget;")
cur.close()
conn.close()
print("Schema dropped successfully.")
