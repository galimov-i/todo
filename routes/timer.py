"""Timer management endpoints."""
from flask import Blueprint, jsonify, request
from models.task import Task
from models.time_entry import TimeEntry
from config import TaskStatus

timer_bp = Blueprint('timer', __name__, url_prefix='/api/timer')


@timer_bp.route('/<int:task_id>/start', methods=['POST'])
def start_timer(task_id):
    """Manually start timer for a task.
    
    Note: This is primarily for manual control. The main auto-start
    happens when moving tasks to 'in_progress' status.
    """
    task = Task.get_by_id(task_id)
    
    if task is None:
        return jsonify({'error': 'Task not found'}), 404
    
    # Check if timer is already running
    active = TimeEntry.get_active_entry(task_id)
    if active:
        return jsonify({
            'message': 'Timer already running',
            'entry': active.to_dict()
        })
    
    entry = TimeEntry.start_timer(task_id)
    
    return jsonify({
        'message': 'Timer started',
        'entry': entry.to_dict()
    })


@timer_bp.route('/<int:task_id>/stop', methods=['POST'])
def stop_timer(task_id):
    """Manually stop timer for a task."""
    task = Task.get_by_id(task_id)
    
    if task is None:
        return jsonify({'error': 'Task not found'}), 404
    
    entry = TimeEntry.stop_timer(task_id)
    
    if entry is None:
        return jsonify({'message': 'No active timer to stop'})
    
    return jsonify({
        'message': 'Timer stopped',
        'entry': entry.to_dict(),
        'duration_formatted': TimeEntry.format_duration(entry.duration)
    })


@timer_bp.route('/<int:task_id>/status', methods=['GET'])
def get_timer_status(task_id):
    """Get current timer status for a task."""
    task = Task.get_by_id(task_id)
    
    if task is None:
        return jsonify({'error': 'Task not found'}), 404
    
    active = TimeEntry.get_active_entry(task_id)
    total_time = TimeEntry.get_total_time(task_id)
    
    return jsonify({
        'task_id': task_id,
        'is_running': active is not None,
        'active_entry': active.to_dict() if active else None,
        'total_time': total_time,
        'total_time_formatted': TimeEntry.format_duration(total_time)
    })


@timer_bp.route('/<int:task_id>/entries', methods=['GET'])
def get_time_entries(task_id):
    """Get all time entries for a task."""
    task = Task.get_by_id(task_id)
    
    if task is None:
        return jsonify({'error': 'Task not found'}), 404
    
    entries = TimeEntry.get_by_task(task_id)
    total_time = TimeEntry.get_total_time(task_id)
    
    return jsonify({
        'task_id': task_id,
        'entries': [e.to_dict() for e in entries],
        'total_time': total_time,
        'total_time_formatted': TimeEntry.format_duration(total_time)
    })


@timer_bp.route('/active', methods=['GET'])
def get_all_active_timers():
    """Get all tasks with active timers."""
    from database.db import get_db
    import time
    
    db = get_db()
    now = int(time.time() * 1000)
    
    # Get all active time entries with task info
    rows = db.execute('''
        SELECT t.*, te.id as entry_id, te.start_time
        FROM tasks t
        JOIN time_entries te ON t.id = te.task_id
        WHERE te.end_time IS NULL
        ORDER BY te.start_time
    ''').fetchall()
    
    result = []
    for row in rows:
        elapsed = (now - row['start_time']) // 1000
        total_time = TimeEntry.get_total_time(row['id'])
        
        result.append({
            'task_id': row['id'],
            'task_title': row['title'],
            'task_status': row['status'],
            'entry_id': row['entry_id'],
            'start_time': row['start_time'],
            'elapsed_seconds': elapsed,
            'elapsed_formatted': TimeEntry.format_duration(elapsed),
            'total_time': total_time,
            'total_time_formatted': TimeEntry.format_duration(total_time)
        })
    
    return jsonify(result)
