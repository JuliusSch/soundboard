import sqlite3
from typing import Tuple, Optional, List

DB_PATH = 'soundboard.db'

def execute_query(query: str, params: Tuple = (), commit: bool = True, fetch: bool = False) -> Optional[List[Tuple]]:
    conn = sqlite3.connect(DB_PATH)
    try:
        cursor = conn.cursor()
        cursor.execute(query, params)

        if commit:
            conn.commit()

        if fetch:
            return cursor.fetchall()

        return None
    finally:
        conn.close()

def init_db():
    execute_query('''
        CREATE TABLE IF NOT EXISTS tracks
        (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            file_path TEXT NOT NULL,
            tags TEXT,
            duration REAL DEFAULT 0
        )'''
    )

    execute_query('''
        CREATE TABLE IF NOT EXISTS selected_tracks
        (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            track_id INTEGER NOT NULL,
            position INTEGER NOT NULL,
            configuration_id INTEGER DEFAULT 1,
            FOREIGN KEY (track_id) REFERENCES tracks (id)
        )'''
    )

def add_track(title, file_path, tags="", duration: float=0.0):
    execute_query('''
         INSERT INTO tracks (title, file_path, tags, duration)
            VALUES (?, ?, ?, ?)''',
        (title, file_path, tags, duration))

def get_all_tracks():
    return execute_query('SELECT * FROM tracks', fetch=True)

def get_track_path_from_selected_track_id(selected_track_id):
    return execute_query('''
        SELECT t.file_path
               FROM selected_tracks st
               JOIN tracks t ON st.track_id = t.id
               WHERE st.id=?
        ''', (selected_track_id,), fetch=True)

def get_selected_tracks(configuration_id=1):
    return execute_query('''
        SELECT t.id, t.title, t.file_path, t.tags, t.duration, st.position, st.id
           FROM selected_tracks st
           JOIN tracks t ON st.track_id = t.id
           WHERE st.configuration_id=?
           ORDER BY st.position
        ''', (configuration_id,), fetch=True)

def save_selected_tracks(tracks, configuration_id=1):
    execute_query("DELETE FROM selected_tracks WHERE configuration_id=?", (configuration_id,))

    for position, track_id in enumerate(tracks):
        execute_query("INSERT INTO selected_tracks (track_id, position, configuration_id) VALUES (?, ?, ?)",
                  (track_id, position, configuration_id))