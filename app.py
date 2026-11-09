import os
import time

import psycopg
from flask import Flask, jsonify, request
from psycopg.rows import dict_row

app = Flask(__name__)


def connect():
    return psycopg.connect(
        host=os.getenv("DB_HOST", "db"),
        port=int(os.getenv("DB_PORT", "5432")),
        dbname=os.getenv("DB_NAME", "campus"),
        user=os.getenv("DB_USER", "campus"),
        password=os.getenv("DB_PASSWORD", "dev-password"),
        connect_timeout=3,
        row_factory=dict_row,
    )


def initialize_database():
    for attempt in range(30):
        try:
            with connect() as connection:
                connection.execute(
                    """CREATE TABLE IF NOT EXISTS tasks (
                           id SERIAL PRIMARY KEY,
                           title TEXT NOT NULL,
                           done BOOLEAN NOT NULL DEFAULT FALSE,
                           created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                       )"""
                )
            return
        except psycopg.OperationalError:
            if attempt == 29:
                raise
            time.sleep(1)


@app.get("/health")
def health():
    try:
        with connect() as connection:
            connection.execute("SELECT 1")
        return jsonify(status="ok", database="reachable"), 200
    except psycopg.Error:
        return jsonify(status="error", database="unreachable"), 503


@app.get("/tasks")
def list_tasks():
    with connect() as connection:
        rows = connection.execute(
            "SELECT id, title, done, created_at FROM tasks ORDER BY id"
        ).fetchall()
    return jsonify(rows)


@app.post("/tasks")
def create_task():
    payload = request.get_json(silent=True) or {}
    title = payload.get("title")
    if not isinstance(title, str) or not title.strip():
        return jsonify(error="title is required"), 400
    with connect() as connection:
        task = connection.execute(
            "INSERT INTO tasks (title) VALUES (%s) "
            "RETURNING id, title, done, created_at",
            (title.strip(),),
        ).fetchone()
    return jsonify(task), 201


if __name__ == "__main__":
    initialize_database()
    app.run(host="0.0.0.0", port=8080)
