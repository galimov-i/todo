"""Task model for Kanban board."""
import time
from database.db import get_db
from config import TaskStatus


class Task:
    """Task model with CRUD operations."""
    
    def __init__(self, id=None, title=None, description=None, status=TaskStatus.TODO,
                 position=0, created_at=None, updated_at=None):
        self.id = id
        self.title = title
        self.description = description
        self.status = status
        self.position = position
        self.created_at = created_at
        self.updated_at = updated_at
    
    @staticmethod
    def from_row(row):
        """Create Task instance from database row."""
        if row is None:
            return None
        return Task(
            id=row['id'],
            title=row['title'],
            description=row['description'],
            status=row['status'],
            position=row['position'],
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )
    
    def to_dict(self):
        """Convert task to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'position': self.position,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
    
    @staticmethod
    def get_all():
        """Get all tasks ordered by status and position."""
        db = get_db()
        rows = db.execute('''
            SELECT * FROM tasks 
            ORDER BY status, position
        ''').fetchall()
        return [Task.from_row(row) for row in rows]
    
    @staticmethod
    def get_by_id(task_id):
        """Get a task by ID."""
        db = get_db()
        row = db.execute(
            'SELECT * FROM tasks WHERE id = ?',
            (task_id,)
        ).fetchone()
        return Task.from_row(row)
    
    @staticmethod
    def get_by_status(status):
        """Get tasks by status, ordered by position."""
        db = get_db()
        rows = db.execute('''
            SELECT * FROM tasks 
            WHERE status = ? 
            ORDER BY position
        ''', (status,)).fetchall()
        return [Task.from_row(row) for row in rows]
    
    def save(self):
        """Save task to database (insert or update)."""
        db = get_db()
        now = int(time.time() * 1000)
        
        if self.id is None:
            # Insert new task
            self.created_at = now
            self.updated_at = now
            
            # Get next position for this status
            result = db.execute('''
                SELECT COALESCE(MAX(position), -1) + 1 as next_pos 
                FROM tasks WHERE status = ?
            ''', (self.status,)).fetchone()
            self.position = result['next_pos']
            
            cursor = db.execute('''
                INSERT INTO tasks (title, description, status, position, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (self.title, self.description, self.status, self.position, 
                  self.created_at, self.updated_at))
            self.id = cursor.lastrowid
        else:
            # Update existing task
            self.updated_at = now
            db.execute('''
                UPDATE tasks 
                SET title = ?, description = ?, status = ?, position = ?, updated_at = ?
                WHERE id = ?
            ''', (self.title, self.description, self.status, self.position,
                  self.updated_at, self.id))
        
        db.commit()
        return self
    
    def delete(self):
        """Delete task from database."""
        if self.id is None:
            return False
        db = get_db()
        db.execute('DELETE FROM tasks WHERE id = ?', (self.id,))
        db.commit()
        return True
    
    def update_status(self, new_status, new_position=None):
        """Update task status and optionally position."""
        if new_status not in TaskStatus.ALL:
            raise ValueError(f"Invalid status: {new_status}")
        
        old_status = self.status
        self.status = new_status
        
        if new_position is not None:
            self.position = new_position
        else:
            # Get next position in new column
            db = get_db()
            result = db.execute('''
                SELECT COALESCE(MAX(position), -1) + 1 as next_pos 
                FROM tasks WHERE status = ?
            ''', (new_status,)).fetchone()
            self.position = result['next_pos']
        
        self.save()
        return old_status
    
    @staticmethod
    def reorder_in_column(status, task_ids):
        """Reorder tasks within a column based on provided order."""
        db = get_db()
        now = int(time.time() * 1000)
        
        for position, task_id in enumerate(task_ids):
            db.execute('''
                UPDATE tasks 
                SET position = ?, updated_at = ?
                WHERE id = ? AND status = ?
            ''', (position, now, task_id, status))
        
        db.commit()
