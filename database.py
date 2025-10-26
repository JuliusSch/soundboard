import sqlite3

def init_db():
    conn = sqlite3.connect('soundboard.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tracks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            file_path TEXT NOT NULL,
            tags TEXT
        )
    ''')
    conn.commit()
    conn.close()

def add_track(title, file_path, tags=""):
    conn = sqlite3.connect('soundboard.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO tracks (title, file_path, tags) VALUES (?, ?, ?)',
                   (title, file_path, tags))
    conn.commit()
    conn.close()

def get_all_tracks():
    conn = sqlite3.connect('soundboard.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM tracks')
    tracks = cursor.fetchall()
    conn.close()
    return tracks
