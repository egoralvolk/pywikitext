# -*- coding: utf-8 -*-
import pymysql

conn = pymysql.connect(host='localhost', port=3306, user='root', passwd='',charset='utf8', db='wikiparse')

cur = conn.cursor()
cur.execute("SELECT * FROM users")

print(cur.description)
print()

for row in cur:
    print(row)

cur.close()
conn.close()