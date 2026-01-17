"""Time entry model for tracking time spent on tasks."""
import time
from database.db import get_db


class TimeEntry:
    """Time entry model for task time tracking."""
    
    def __init__(self, id=None, task_id=None, start_time=None, 
                 end_time=None, duration=None, created_at=None):
        self.id = id
        self.task_id = task_id
        self.start_time = start_time
        self.end_time = end_time
        self.duration = duration
        self.created_at = created_at
    
    @staticmethod
    def from_row(row):
        """Create TimeEntry instance from database row."""
        if row is None:
            return None
        return TimeEntry(
            id=row['id'],
            task_id=row['task_id'],
            start_time=row['start_time'],
            end_time=row['end_time'],
            duration=row['duration'],
            created_at=row['created_at']
        )
    
    def to_dict(self):
        """Convert time entry to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'task_id': self.task_id,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'duration': self.duration,
            'created_at': self.created_at
        }
    
    @staticmethod
    def get_by_task(task_id):
        """Get all time entries for a task."""
        db = get_db()
        rows = db.execute('''
            SELECT * FROM time_entries 
            WHERE task_id = ? 
            ORDER BY start_time DESC
        ''', (task_id,)).fetchall()
        return [TimeEntry.from_row(row) for row in rows]
    
    @staticmethod
    def get_active_entry(task_id):
        """Get active (running) time entry for a task."""
        db = get_db()
        row = db.execute('''
            SELECT * FROM time_entries 
            WHERE task_id = ? AND end_time IS NULL
            ORDER BY start_time DESC
            LIMIT 1
        ''', (task_id,)).fetchone()
        return TimeEntry.from_row(row)
    
    @staticmethod
    def start_timer(task_id):
        """Start a new timer for a task.
        
        Stops any existing active timer first.
        """
        # First, stop any active timer for this task
        TimeEntry.stop_timer(task_id)
        
        db = get_db()
        now = int(time.time() * 1000)
        
        cursor = db.execute('''
            INSERT INTO time_entries (task_id, start_time, end_time, duration, created_at)
            VALUES (?, ?, NULL, NULL, ?)
        ''', (task_id, now, now))
        
        db.commit()
        
        return TimeEntry(
            id=cursor.lastrowid,
            task_id=task_id,
            start_time=now,
            end_time=None,
            duration=None,
            created_at=now
        )
    
    @staticmethod
    def stop_timer(task_id):
        """Stop active timer for a task.
        
        Returns the stopped entry or None if no active timer.
        """
        db = get_db()
        now = int(time.time() * 1000)
        
        # Find active entry
        row = db.execute('''
            SELECT * FROM time_entries 
            WHERE task_id = ? AND end_time IS NULL
        ''', (task_id,)).fetchone()
        
        if row is None:
            return None
        
        entry = TimeEntry.from_row(row)
        
        # Calculate duration in seconds
        duration = (now - entry.start_time) // 1000
        
        # Update entry
        db.execute('''
            UPDATE time_entries 
            SET end_time = ?, duration = ?
            WHERE id = ?
        ''', (now, duration, entry.id))
        
        db.commit()
        
        entry.end_time = now
        entry.duration = duration
        
        return entry
    
    @staticmethod
    def get_total_time(task_id):
        """Get total time spent on a task in seconds.
        
        Includes time from completed entries plus elapsed time
        from any active entry.
        """
        db = get_db()
        now = int(time.time() * 1000)
        
        # Sum of completed entries
        result = db.execute('''
            SELECT COALESCE(SUM(duration), 0) as total
            FROM time_entries 
            WHERE task_id = ? AND end_time IS NOT NULL
        ''', (task_id,)).fetchone()
        
        total = result['total']
        
        # Add time from active entry if exists
        active = db.execute('''
            SELECT start_time FROM time_entries 
            WHERE task_id = ? AND end_time IS NULL
            LIMIT 1
        ''', (task_id,)).fetchone()
        
        if active:
            elapsed = (now - active['start_time']) // 1000
            total += elapsed
        
        return total
    
    @staticmethod
    def get_active_start_time(task_id):
        """Get the start time of the active timer, or None."""
        db = get_db()
        row = db.execute('''
            SELECT start_time FROM time_entries 
            WHERE task_id = ? AND end_time IS NULL
            LIMIT 1
        ''', (task_id,)).fetchone()
        
        return row['start_time'] if row else None
    
    @staticmethod
    def format_duration(seconds):
        """Format duration in seconds to HH:MM:SS string."""
        if seconds is None or seconds < 0:
            return "00:00:00"
        
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
