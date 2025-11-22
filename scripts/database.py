import sqlite3
from typing import Tuple, Optional, List

from scripts.data_models import Track, SelectedTrack, Panel

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
            panel_id INTEGER DEFAULT 0,
            FOREIGN KEY (track_id) REFERENCES tracks (id)
        )'''
    )

    execute_query('''
        CREATE TABLE IF NOT EXISTS panels
        (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            volume REAL DEFAULT 0.5,
            loop_enabled INTEGER DEFAULT 0,
            fade_enabled INTEGER DEFAULT 0
        )'''
    )

def add_track(title, file_path, tags="", duration: float=0.0):
    execute_query('''
        INSERT INTO tracks (title, file_path, tags, duration)
        VALUES (?, ?, ?, ?)''', (title, file_path, tags, duration))

def get_all_tracks():
    tracks = execute_query('SELECT * FROM tracks', fetch=True)
    return [Track(*track) for track in tracks]

def get_selected_track(track_id, panel_id):
    track = execute_query('''
        SELECT st.id, t.title, t.file_path, t.duration, st.track_id, st.position, st.panel_id
        FROM selected_tracks st
        JOIN tracks t ON st.track_id = t.id
        WHERE st.track_id=? AND st.panel_id=?
        ORDER BY st.position
        ''', (track_id, panel_id), fetch=True)
    if len(track) == 1:
        return SelectedTrack(*track[0])
    return None

def get_selected_tracks(panel_id):
    selected_tracks = execute_query('''
        SELECT st.id, t.title, t.file_path, t.duration, st.track_id, st.position, st.panel_id
        FROM selected_tracks st
        JOIN tracks t ON st.track_id = t.id
        WHERE st.panel_id=?
        ORDER BY st.position
        ''', (panel_id,), fetch=True)
    return [SelectedTrack(*track) for track in selected_tracks]

def add_selected_track(track_id, panel_id):
    tracks = get_selected_tracks(panel_id)
    execute_query('''
        INSERT INTO selected_tracks (track_id, position, panel_id)
        VALUES (?,?,?)''', (track_id, len(tracks), panel_id))

def remove_selected_track(selected_track_id):
    execute_query('''
        DELETE FROM selected_tracks WHERE id=?''', (selected_track_id,))

def add_panel(name: str, panel_id: int = 1, volume: float = 1.0):
    execute_query('''
        INSERT INTO panels (name, id, volume)
        VALUES (?, ?, ?)''', (name, panel_id, volume))

def get_panels():
    panels = execute_query('SELECT * FROM panels', fetch=True)
    return [Panel(*panel) for panel in panels]

def set_panel_volume(panel_id: int, volume: float):
    execute_query('UPDATE panels SET volume=? WHERE id=?', (volume, panel_id))

def get_panel_volume(panel_id: int):
    volume = execute_query('SELECT volume FROM panels WHERE id=?', (panel_id,), fetch=True)
    return volume[0][0]