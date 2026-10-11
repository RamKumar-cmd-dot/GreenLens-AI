"""SQLite snapshot import, only when source content changes. No generation/training."""

import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd
from ml.common import DATA, TARGETS

INTERACTION_ACTIONS = {
    "explore",
    "dismiss",
    "remind_later",
    "not_interested",
    "interested",
    "clear",
}


class Store:
    def __init__(self, path):
        self.path = str(path)
        Path(path).parent.mkdir(parents=True, exist_ok=True)

    def connect(self):
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    def initialize(self):
        paths = [
            DATA / "processed/customer_360.csv",
            DATA / "synthetic/transactions.csv",
            DATA / "synthetic/customer_products.csv",
        ]
        digest = hashlib.sha256(b"".join(p.read_bytes() for p in paths)).hexdigest()
        with self.connect() as db:
            db.execute(
                "CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY, value TEXT)"
            )
            # Additive migration: interaction history survives source-snapshot refreshes.
            db.execute("""CREATE TABLE IF NOT EXISTS customer_interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id TEXT NOT NULL,
                product_id TEXT NOT NULL,
                action TEXT NOT NULL CHECK(action IN ('explore','dismiss','remind_later','not_interested','interested','clear')),
                reason TEXT,
                created_at TEXT NOT NULL,
                snooze_until TEXT
            )""")
            db.execute(
                "CREATE INDEX IF NOT EXISTS interaction_customer_product_latest ON customer_interactions(customer_id, product_id, created_at DESC, id DESC)"
            )
            row = db.execute(
                "SELECT value FROM metadata WHERE key='source_hash'"
            ).fetchone()
            if row and row["value"] == digest:
                return
            features = pd.read_csv(paths[0])
            records = json.loads(features.to_json(orient="records"))
            db.execute("DROP TABLE IF EXISTS customers")
            db.execute(
                "CREATE TABLE customers (customer_id TEXT PRIMARY KEY, region TEXT, age_band TEXT, payload TEXT)"
            )
            db.executemany(
                "INSERT INTO customers VALUES (?,?,?,?)",
                [
                    (
                        r["customer_id"],
                        r["region"],
                        r["age_band"],
                        json.dumps(r, allow_nan=False),
                    )
                    for r in records
                ],
            )
            pd.read_csv(paths[1]).to_sql(
                "transactions", db, if_exists="replace", index=False
            )
            pd.read_csv(paths[2]).to_sql(
                "products", db, if_exists="replace", index=False
            )
            db.execute(
                "CREATE INDEX IF NOT EXISTS tx_customer_date ON transactions(customer_id, transaction_date)"
            )
            db.execute(
                "CREATE INDEX IF NOT EXISTS products_customer ON products(customer_id)"
            )
            db.execute(
                "INSERT OR REPLACE INTO metadata VALUES (?,?)", ("source_hash", digest)
            )

    def customer_exists(self, cid):
        with self.connect() as db:
            return (
                db.execute(
                    "SELECT 1 FROM customers WHERE customer_id=?", (cid,)
                ).fetchone()
                is not None
            )

    def record_interaction(
        self, cid, product_id, action, reason=None, snooze_until=None
    ):
        if not self.customer_exists(cid):
            raise KeyError(cid)
        if product_id not in TARGETS:
            raise ValueError("Unknown product_id")
        if action not in INTERACTION_ACTIONS:
            raise ValueError("Unknown interaction action")
        if reason is not None:
            reason = str(reason).strip() or None
            if reason is not None and len(reason) > 500:
                raise ValueError("reason must be 500 characters or fewer")
        if action == "remind_later":
            if not snooze_until:
                raise ValueError("snooze_until is required for remind_later")
            parsed = datetime.fromisoformat(str(snooze_until).replace("Z", "+00:00"))
            if parsed.tzinfo is None:
                raise ValueError("snooze_until must include a timezone")
            parsed = parsed.astimezone(timezone.utc)
            if parsed <= datetime.now(timezone.utc):
                raise ValueError("snooze_until must be in the future")
            snooze_until = parsed.isoformat(timespec="seconds").replace("+00:00", "Z")
        elif snooze_until is not None:
            raise ValueError("snooze_until is only valid for remind_later")
        created_at = (
            datetime.now(timezone.utc)
            .isoformat(timespec="seconds")
            .replace("+00:00", "Z")
        )
        with self.connect() as db:
            cursor = db.execute(
                "INSERT INTO customer_interactions (customer_id,product_id,action,reason,created_at,snooze_until) VALUES (?,?,?,?,?,?)",
                (cid, product_id, action, reason, created_at, snooze_until),
            )
            row = db.execute(
                "SELECT * FROM customer_interactions WHERE id=?", (cursor.lastrowid,)
            ).fetchone()
        return dict(row)

    def latest_interaction(self, cid, product_id):
        with self.connect() as db:
            row = db.execute(
                "SELECT * FROM customer_interactions WHERE customer_id=? AND product_id=? ORDER BY created_at DESC,id DESC LIMIT 1",
                (cid, product_id),
            ).fetchone()
        return dict(row) if row else None

    def interaction_history(self, cid, offset=0, limit=50):
        if not self.customer_exists(cid):
            raise KeyError(cid)
        with self.connect() as db:
            total = db.execute(
                "SELECT count(*) FROM customer_interactions WHERE customer_id=?", (cid,)
            ).fetchone()[0]
            rows = db.execute(
                "SELECT * FROM customer_interactions WHERE customer_id=? ORDER BY created_at DESC,id DESC LIMIT ? OFFSET ?",
                (cid, limit, offset),
            ).fetchall()
        return {
            "total": total,
            "offset": offset,
            "limit": limit,
            "items": [dict(row) for row in rows],
        }

    def customer(self, cid):
        with self.connect() as db:
            row = db.execute(
                "SELECT payload FROM customers WHERE customer_id=?", (cid,)
            ).fetchone()
            if row is None:
                raise KeyError(cid)
            features = json.loads(row["payload"])
            products = [
                dict(r)
                for r in db.execute(
                    "SELECT * FROM products WHERE customer_id=?", (cid,)
                )
            ]
        return {
            "customer_id": cid,
            "features": features,
            "data_timestamp": features["data_timestamp"],
            "synthetic": True,
            "products": products,
        }

    def customers(self, offset, limit, region=None, query=None):
        where = []
        args = []
        if region:
            where.append("region=?")
            args.append(region)
        if query:
            where.append("customer_id LIKE ?")
            args.append(f"%{query}%")
        clause = " WHERE " + " AND ".join(where) if where else ""
        with self.connect() as db:
            total = db.execute(
                "SELECT count(*) FROM customers" + clause, args
            ).fetchone()[0]
            ids = [
                r[0]
                for r in db.execute(
                    "SELECT customer_id FROM customers"
                    + clause
                    + " ORDER BY customer_id LIMIT ? OFFSET ?",
                    [*args, limit, offset],
                )
            ]
        return {
            "total": total,
            "offset": offset,
            "limit": limit,
            "items": [self.customer(cid) for cid in ids],
        }

    def transactions(self, cid, offset, limit, category=None):
        self.customer(cid)
        clause = "customer_id=?"
        args = [cid]
        if category:
            clause += " AND sustainability_category=?"
            args.append(category)
        with self.connect() as db:
            total = db.execute(
                "SELECT count(*) FROM transactions WHERE " + clause, args
            ).fetchone()[0]
            items = [
                dict(r)
                for r in db.execute(
                    "SELECT * FROM transactions WHERE "
                    + clause
                    + " ORDER BY transaction_date DESC, transaction_id LIMIT ? OFFSET ?",
                    [*args, limit, offset],
                )
            ]
        return {"total": total, "offset": offset, "limit": limit, "items": items}

    def all_features(self):
        with self.connect() as db:
            return pd.DataFrame(
                [
                    json.loads(r[0])
                    for r in db.execute(
                        "SELECT payload FROM customers ORDER BY customer_id"
                    )
                ]
            )

    def spending(self, cid):
        with self.connect() as db:
            return [
                dict(r)
                for r in db.execute(
                    "SELECT substr(transaction_date,1,7) AS month, sustainability_category AS category, round(sum(amount_gbp),2) AS amount_gbp FROM transactions WHERE customer_id=? GROUP BY month,category ORDER BY month,category",
                    (cid,),
                )
            ]

    def business_trends(self):
        with self.connect() as db:
            return [
                dict(r)
                for r in db.execute(
                    "SELECT substr(transaction_date,1,7) AS month, sustainability_category AS category, round(sum(amount_gbp),2) AS amount_gbp FROM transactions GROUP BY month,category ORDER BY month,category"
                )
            ]
