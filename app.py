"""Учебный сервис заметок для домашнего задания № 2 по DevOps."""

import os
import socket
from urllib.parse import unquote, urlparse

from flask import Flask, jsonify, request

STUDENT = "Красильникова Юлия Александровна"
GROUP = "БИСТ-23-ПО-3"
MARKER_DEFAULT = "sitelab"

MARKER = os.environ.get("MARKER", MARKER_DEFAULT)
APP_PORT = int(os.environ.get("APP_PORT", "5001"))
DATABASE_URL = os.environ.get("DATABASE_URL", "")

app = Flask(__name__)
app.json.ensure_ascii = False


def db_params():
    """Преобразовать URL PostgreSQL или MariaDB в параметры драйвера."""
    url = urlparse(DATABASE_URL)
    if url.scheme not in ("postgresql", "mysql"):
        raise RuntimeError("DATABASE_URL не задан или имеет неизвестную схему")
    return url.scheme, {
        "host": url.hostname,
        "port": url.port or (5432 if url.scheme == "postgresql" else 3306),
        "user": unquote(url.username or ""),
        "password": unquote(url.password or ""),
        "database": url.path.lstrip("/"),
    }


def connect():
    kind, params = db_params()
    if kind == "postgresql":
        import psycopg2

        params["dbname"] = params.pop("database")
        return kind, psycopg2.connect(connect_timeout=5, **params)
    import MySQLdb

    return kind, MySQLdb.connect(connect_timeout=5, **params)


DDL = {
    "postgresql": "CREATE TABLE IF NOT EXISTS notes ("
    "id SERIAL PRIMARY KEY, text VARCHAR(200) NOT NULL, "
    "host VARCHAR(64) NOT NULL, version VARCHAR(32) NOT NULL, "
    "created TIMESTAMP DEFAULT now())",
    "mysql": "CREATE TABLE IF NOT EXISTS notes ("
    "id INT AUTO_INCREMENT PRIMARY KEY, text VARCHAR(200) NOT NULL, "
    "host VARCHAR(64) NOT NULL, version VARCHAR(32) NOT NULL, "
    "created TIMESTAMP DEFAULT CURRENT_TIMESTAMP)",
}


def version():
    try:
        with open("/app/VERSION", encoding="utf-8") as version_file:
            return version_file.read().strip() or "dev"
    except OSError:
        return "dev"


def describe(error):
    cause = error.__cause__ or error.__context__
    if cause is None or str(cause) in str(error):
        return str(error)
    return f"{error} ({cause})"


def with_db(action):
    try:
        kind, connection = connect()
    except Exception as error:  # noqa: BLE001
        return jsonify(error="нет связи с базой", detail=describe(error)), 503
    try:
        cursor = connection.cursor()
        cursor.execute(DDL[kind])
        result = action(cursor)
        connection.commit()
        return result
    except Exception as error:  # noqa: BLE001
        return jsonify(error="ошибка запроса к базе", detail=describe(error)), 503
    finally:
        connection.close()


@app.get("/")
def index():
    return f"probe: {MARKER}, host {socket.gethostname()}\n"


@app.get("/me")
def me():
    try:
        kind, params = db_params()
        database = f"{kind} {params['host']}:{params['port']}"
    except (RuntimeError, ValueError) as error:
        database = str(error)
    return jsonify(student=STUDENT, group=GROUP, marker=MARKER,
                   hostname=socket.gethostname(), version=version(), database=database)


@app.post("/notes")
def add_note():
    text = request.form.get("text", "").strip()
    if not text:
        return jsonify(error="empty note"), 400

    def insert(cursor):
        cursor.execute("INSERT INTO notes (text, host, version) VALUES (%s, %s, %s)",
                       (text[:200], socket.gethostname(), version()))
        return jsonify(saved=text[:200], hostname=socket.gethostname(), version=version()), 201

    return with_db(insert)


@app.get("/notes")
def list_notes():
    def select(cursor):
        cursor.execute("SELECT id, text, host, version, created FROM notes ORDER BY id")
        rows = [dict(id=row[0], text=row[1], host=row[2], version=row[3], created=str(row[4]))
                for row in cursor.fetchall()]
        return jsonify(hostname=socket.gethostname(), version=version(), count=len(rows), notes=rows)

    return with_db(select)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=APP_PORT)
