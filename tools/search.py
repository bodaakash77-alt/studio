#!/usr/bin/env python3
import sqlite3, os, sys
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
q=' '.join(sys.argv[1:]) or '*'
c=sqlite3.connect(os.path.join(ROOT,'catalog','catalog.db'))
terms=' OR '.join(t+'*' for t in q.replace('"',' ').split())
rows=c.execute("select a.id,a.category,a.license,a.path,a.description from fts f join assets a on a.id=f.id where fts match ? order by rank limit 25",(terms,)).fetchall()
for r in rows: print(f"{r[0]:32} {r[1]:10} {r[2]:10} {r[3]}\n    {r[4][:110]}")
print(len(rows),'result(s)')
