import sqlite3
from datetime import datetime


DB_PATH = "navigator.db"


def get_connection(db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path=DB_PATH):
    with get_connection(db_path) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS routes (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                start_point     TEXT NOT NULL,
                finish_point    TEXT NOT NULL,
                route           TEXT NOT NULL,
                distance        REAL NOT NULL,
                time            REAL NOT NULL,
                traffic         REAL NOT NULL,
                created_at      TEXT NOT NULL,
                actual_time     REAL,
                actual_distance REAL,
                user_name       TEXT NOT NULL DEFAULT 'guest',
                user_type       TEXT NOT NULL DEFAULT 'student'
            )
        """)


def save_route(start, finish, path, distance, time, traffic,
               user_name="guest", user_type="student", db_path=DB_PATH):
    with get_connection(db_path) as conn:
        cursor = conn.execute(
            """
            INSERT INTO routes
                (start_point, finish_point, route, distance, time, traffic,
                 created_at, user_name, user_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (start, finish, ",".join(path), distance, time, traffic,
             datetime.now().isoformat(timespec="seconds"), user_name, user_type),
        )
        return cursor.lastrowid


def update_actual(route_id, actual_time, actual_distance, db_path=DB_PATH):
    with get_connection(db_path) as conn:
        cursor = conn.execute(
            "UPDATE routes SET actual_time = ?, actual_distance = ? WHERE id = ?",
            (actual_time, actual_distance, route_id),
        )
        return cursor.rowcount > 0


def get_all_routes(db_path=DB_PATH):
    with get_connection(db_path) as conn:
        rows = conn.execute("SELECT * FROM routes ORDER BY id DESC").fetchall()
        return [dict(row) for row in rows]

init_db()