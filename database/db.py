"""Database initialization and connection management."""
import sqlite3
import os
from flask import g, current_app

def get_db():
    """Get database connection for the current request.
    
    Creates a new connection if one doesn't exist for this request.
    Uses Row factory for dict-like access to query results.
    """
    if 'db' not in g:
        g.db = sqlite3.connect(
            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row
        # Enable foreign keys
        g.db.execute('PRAGMA foreign_keys = ON')
    return g.db

def close_db(e=None):
    """Close database connection at end of request."""
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    """Initialize the database with schema."""
    from config import DATABASE_PATH
    
    # Create database directory if it doesn't exist
    db_dir = os.path.dirname(DATABASE_PATH)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir)
    
    # Connect and create schema
    conn = sqlite3.connect(DATABASE_PATH)
    conn.execute('PRAGMA foreign_keys = ON')
    
    # Read and execute schema
    schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
    with open(schema_path, 'r') as f:
        conn.executescript(f.read())
    
    conn.commit()
    conn.close()
    print(f"Database initialized at {DATABASE_PATH}")

def init_app(app):
    """Register database functions with Flask app."""
    app.teardown_appcontext(close_db)

def seed_db():
    """Add sample data for testing."""
    import time
    from config import DATABASE_PATH
    
    conn = sqlite3.connect(DATABASE_PATH)
    conn.execute('PRAGMA foreign_keys = ON')
    cursor = conn.cursor()
    
    now = int(time.time() * 1000)  # Current time in milliseconds
    
    # Sample tasks
    tasks = [
        ('Design database schema', 'Create tables for tasks and time entries', 'done', 0, now, now),
        ('Setup Flask backend', 'Initialize Flask app with routes', 'done', 1, now, now),
        ('Implement task CRUD', 'Create, read, update, delete endpoints', 'in_progress', 0, now, now),
        ('Build drag-and-drop UI', 'Use HTML5 drag and drop API', 'todo', 0, now, now),
        ('Add timer logic', 'Auto-start/stop timers on status change', 'todo', 1, now, now),
        ('Test application', 'Verify all features work correctly', 'waiting', 0, now, now),
    ]
    
    cursor.executemany('''
        INSERT INTO tasks (title, description, status, position, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', tasks)
    
    # Add a sample time entry for the in_progress task
    cursor.execute('SELECT id FROM tasks WHERE status = "in_progress" LIMIT 1')
    task = cursor.fetchone()
    if task:
        # Active time entry (no end_time)
        cursor.execute('''
            INSERT INTO time_entries (task_id, start_time, end_time, duration, created_at)
            VALUES (?, ?, NULL, NULL, ?)
        ''', (task[0], now - 3600000, now))  # Started 1 hour ago
    
    conn.commit()
    conn.close()
    print("Sample data seeded successfully")

if __name__ == '__main__':
    init_db()
    seed_db()
