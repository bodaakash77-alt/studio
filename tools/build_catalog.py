#!/usr/bin/env python3
"""Build/refresh the searchable asset catalog (SQLite + FTS5) from catalog/manifest.json.
Usage: build_catalog.py            # rebuild DB
       search.py "temple stone"    # query
"""
import json, os, sqlite3, hashlib, datetime, sys
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAN=os.path.join(ROOT,'catalog','manifest.json')
DB=os.path.join(ROOT,'catalog','catalog.db')
def sha(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for c in iter(lambda:f.read(1<<20),b''): h.update(c)
    return h.hexdigest()[:16]
def main():
    items=json.load(open(MAN))
    if os.path.exists(DB): os.remove(DB)
    c=sqlite3.connect(DB)
    c.execute("create table assets(id text primary key,name text,category text,tags text,path text,source text,url text,license text,attribution text,commercial_ok integer,downloaded text,size_bytes integer,sha16 text,description text,tier text)")
    c.execute("create virtual table fts using fts5(id,name,category,tags,description)")
    seen={}
    for it in items:
        p=os.path.join(ROOT,it['path'])
        if not os.path.exists(p): print('MISSING',it['path']); continue
        s=sha(p)
        if s in seen: print('DUPLICATE',it['id'],'==',seen[s]); continue
        seen[s]=it['id']
        c.execute("insert into assets values(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(it['id'],it['name'],it['category'],' '.join(it.get('tags',[])),it['path'],it['source'],it['url'],it['license'],it.get('attribution','none required'),1 if it.get('commercial_ok',True) else 0,it.get('downloaded',''),os.path.getsize(p),s,it.get('description',''),it.get('tier','core')))
        c.execute("insert into fts values(?,?,?,?,?)",(it['id'],it['name'],it['category'],' '.join(it.get('tags',[])),it.get('description','')))
    c.commit();n=c.execute('select count(*) from assets').fetchone()[0];print('catalog rows',n)
if __name__=='__main__': main()
