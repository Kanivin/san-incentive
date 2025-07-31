# load_bulk_sql.py
from django.db import connection

sql_file = 'bulk_insert_deals.sql'

with open(sql_file, 'r') as f:
    sql = f.read()

with connection.cursor() as cursor:
    cursor.executescript(sql)
