#!/usr/bin/env python3
"""Lee feeds de Adafruit IO y los guarda en SQLite sin duplicados."""
import logging
import os
import sqlite3
import time
from datetime import datetime, timezone

import requests

AIO_USER = os.environ["AIO_USERNAME"]
AIO_KEY = os.environ["AIO_KEY"]
FEEDS = [f.strip() for f in os.environ.get("AIO_FEEDS", "temperatura,humedad,luminosidad").split(",")]
DB_PATH = os.environ.get("DB_PATH", r"C:\proyecto\datos\sensores.db")
INTERVALO = int(os.environ.get("INTERVALO", "30"))

BASE_URL = f"https://io.adafruit.com/api/v2/{AIO_USER}/feeds"
HEADERS = {"X-AIO-Key": AIO_KEY}

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def init_db(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS lecturas (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            feed         TEXT NOT NULL,
            aio_id       TEXT NOT NULL UNIQUE,
            valor        TEXT NOT NULL,
            valor_num    REAL,
            creado_en    TEXT NOT NULL,
            insertado_en TEXT NOT NULL
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_feed_fecha ON lecturas(feed, creado_en)")
    conn.commit()


def obtener_datos(feed, limite=100):
    url = f"{BASE_URL}/{feed}/data"
    r = requests.get(url, headers=HEADERS, params={"limit": limite}, timeout=10)
    r.raise_for_status()
    return r.json()


def guardar(conn, feed, datos):
    nuevos = 0
    ahora = datetime.now(timezone.utc).isoformat()
    for d in datos:
        try:
            num = float(d["value"])
        except (ValueError, TypeError):
            num = None
        cur = conn.execute(
            """INSERT OR IGNORE INTO lecturas
               (feed, aio_id, valor, valor_num, creado_en, insertado_en)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (feed, str(d["id"]), d["value"], num, d["created_at"], ahora),
        )
        nuevos += cur.rowcount
    conn.commit()
    return nuevos


def main():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    init_db(conn)
    logging.info("Base de datos: %s | Feeds: %s", DB_PATH, FEEDS)

    while True:
        for feed in FEEDS:
            try:
                nuevos = guardar(conn, feed, obtener_datos(feed))
                logging.info("%s: %d registros nuevos", feed, nuevos)
            except requests.RequestException as e:
                logging.error("Error consultando %s: %s", feed, e)
        time.sleep(INTERVALO)


if __name__ == "__main__":
    main()