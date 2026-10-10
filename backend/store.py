"""SQLite snapshot import, only when source content changes. No generation/training."""
import hashlib
import json
import sqlite3
from pathlib import Path
import pandas as pd
from ml.common import DATA

class Store:
    def __init__(self, path):
        self.path = str(path)
        Path(path).parent.mkdir(parents=True, exist_ok=True)

    def connect(self):
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    def initialize(self):
        paths = [DATA/'processed/customer_360.csv', DATA/'synthetic/transactions.csv', DATA/'synthetic/customer_products.csv']
        digest = hashlib.sha256(b''.join(p.read_bytes() for p in paths)).hexdigest()
        with self.connect() as db:
            db.execute('CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY, value TEXT)')
            row = db.execute("SELECT value FROM metadata WHERE key='source_hash'").fetchone()
            if row and row['value'] == digest:
                return
            features = pd.read_csv(paths[0])
            records = json.loads(features.to_json(orient='records'))
            db.execute('DROP TABLE IF EXISTS customers')
            db.execute('CREATE TABLE customers (customer_id TEXT PRIMARY KEY, region TEXT, age_band TEXT, payload TEXT)')
            db.executemany('INSERT INTO customers VALUES (?,?,?,?)', [(r['customer_id'], r['region'], r['age_band'], json.dumps(r, allow_nan=False)) for r in records])
            pd.read_csv(paths[1]).to_sql('transactions', db, if_exists='replace', index=False)
            pd.read_csv(paths[2]).to_sql('products', db, if_exists='replace', index=False)
            db.execute('CREATE INDEX IF NOT EXISTS tx_customer_date ON transactions(customer_id, transaction_date)')
            db.execute('CREATE INDEX IF NOT EXISTS products_customer ON products(customer_id)')
            db.execute('INSERT OR REPLACE INTO metadata VALUES (?,?)', ('source_hash', digest))

    def customer(self, cid):
        with self.connect() as db:
            row = db.execute('SELECT payload FROM customers WHERE customer_id=?', (cid,)).fetchone()
            if row is None:
                raise KeyError(cid)
            features = json.loads(row['payload'])
            products = [dict(r) for r in db.execute('SELECT * FROM products WHERE customer_id=?', (cid,))]
        return {'customer_id': cid, 'features': features, 'data_timestamp': features['data_timestamp'], 'synthetic': True, 'products': products}

    def customers(self, offset, limit, region=None, query=None):
        where = []; args = []
        if region:
            where.append('region=?'); args.append(region)
        if query:
            where.append('customer_id LIKE ?'); args.append(f'%{query}%')
        clause = ' WHERE ' + ' AND '.join(where) if where else ''
        with self.connect() as db:
            total = db.execute('SELECT count(*) FROM customers'+clause, args).fetchone()[0]
            ids = [r[0] for r in db.execute('SELECT customer_id FROM customers'+clause+' ORDER BY customer_id LIMIT ? OFFSET ?', [*args,limit,offset])]
        return {'total': total, 'offset': offset, 'limit': limit, 'items': [self.customer(cid) for cid in ids]}

    def transactions(self, cid, offset, limit, category=None):
        self.customer(cid)
        clause = 'customer_id=?'; args = [cid]
        if category:
            clause += ' AND sustainability_category=?'; args.append(category)
        with self.connect() as db:
            total = db.execute('SELECT count(*) FROM transactions WHERE '+clause, args).fetchone()[0]
            items = [dict(r) for r in db.execute('SELECT * FROM transactions WHERE '+clause+' ORDER BY transaction_date DESC, transaction_id LIMIT ? OFFSET ?', [*args,limit,offset])]
        return {'total':total,'offset':offset,'limit':limit,'items':items}

    def all_features(self):
        with self.connect() as db:
            return pd.DataFrame([json.loads(r[0]) for r in db.execute('SELECT payload FROM customers ORDER BY customer_id')])

    def spending(self, cid):
        with self.connect() as db:
            return [dict(r) for r in db.execute('SELECT substr(transaction_date,1,7) AS month, sustainability_category AS category, round(sum(amount_gbp),2) AS amount_gbp FROM transactions WHERE customer_id=? GROUP BY month,category ORDER BY month,category',(cid,))]

    def business_trends(self):
        with self.connect() as db:
            return [dict(r) for r in db.execute("SELECT substr(transaction_date,1,7) AS month, sustainability_category AS category, round(sum(amount_gbp),2) AS amount_gbp FROM transactions GROUP BY month,category ORDER BY month,category")]
