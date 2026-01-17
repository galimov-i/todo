"""Task CRUD endpoints."""
from flask import Blueprint, jsonify, request
from models.task import Task
from models.time_entry import TimeEntry
from config import TaskStatus

tasks_bp = Blueprint('tasks', __name__, url_prefix='/api/tasks')


@tasks_bp.route('', methods=['GET'])
def get_all_tasks():
    """Get all tasks grouped by status with time info."""
    tasks = Task.get_all()
    
    # Group by status and add time info
    result = {status: [] for status in TaskStatus.ALL}
    
    for task in tasks:
        task_dict = task.to_dict()
        # Add time tracking info
        task_dict['total_time'] = TimeEntry.get_total_time(task.id)
        task_dict['total_time_formatted'] = TimeEntry.format_duration(task_dict['total_time'])
        task_dict['active_timer_start'] = TimeEntry.get_active_start_time(task.id)
        result[task.status].append(task_dict)
    
    return jsonify(result)


@tasks_bp.route('/<int:task_id>', methods=['GET'])
def get_task(task_id):
    """Get a single task by ID."""
    task = Task.get_by_id(task_id)
    
    if task is None:
        return jsonify({'error': 'Task not found'}), 404
    
    task_dict = task.to_dict()
    task_dict['total_time'] = TimeEntry.get_total_time(task.id)
    task_dict['total_time_formatted'] = TimeEntry.format_duration(task_dict['total_time'])
    task_dict['active_timer_start'] = TimeEntry.get_active_start_time(task.id)
    task_dict['time_entries'] = [e.to_dict() for e in TimeEntry.get_by_task(task.id)]
    
    return jsonify(task_dict)


@tasks_bp.route('', methods=['POST'])
def create_task():
    """Create a new task."""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    title = data.get('title', '').strip()
    if not title:
        return jsonify({'error': 'Title is required'}), 400
    
    description = data.get('description', '').strip()
    status = data.get('status', TaskStatus.TODO)
    
    if status not in TaskStatus.ALL:
        return jsonify({'error': f'Invalid status. Must be one of: {TaskStatus.ALL}'}), 400
    
    task = Task(
        title=title,
        description=description,
        status=status
    )
    task.save()
    
    # If task is created directly in "in_progress", start timer
    if status == TaskStatus.IN_PROGRESS:
        TimeEntry.start_timer(task.id)
    
    task_dict = task.to_dict()
    task_dict['total_time'] = 0
    task_dict['total_time_formatted'] = '00:00:00'
    task_dict['active_timer_start'] = TimeEntry.get_active_start_time(task.id)
    
    return jsonify(task_dict), 201


@tasks_bp.route('/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    """Update a task's title and/or description."""
    task = Task.get_by_id(task_id)
    
    if task is None:
        return jsonify({'error': 'Task not found'}), 404
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    if 'title' in data:
        title = data['title'].strip()
        if not title:
            return jsonify({'error': 'Title cannot be empty'}), 400
        task.title = title
    
    if 'description' in data:
        task.description = data['description'].strip()
    
    task.save()
    
    task_dict = task.to_dict()
    task_dict['total_time'] = TimeEntry.get_total_time(task.id)
    task_dict['total_time_formatted'] = TimeEntry.format_duration(task_dict['total_time'])
    task_dict['active_timer_start'] = TimeEntry.get_active_start_time(task.id)
    
    return jsonify(task_dict)


@tasks_bp.route('/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    """Delete a task and all its time entries."""
    task = Task.get_by_id(task_id)
    
    if task is None:
        return jsonify({'error': 'Task not found'}), 404
    
    # Stop any active timer first
    TimeEntry.stop_timer(task_id)
    
    task.delete()
    
    return jsonify({'message': 'Task deleted successfully'})


@tasks_bp.route('/<int:task_id>/status', methods=['PUT'])
def update_task_status(task_id):
    """Update task status (move between columns).
    
    This endpoint handles timer auto-start/stop logic:
    - Moving TO 'in_progress': starts timer
    - Moving FROM 'in_progress': stops timer
    """
    task = Task.get_by_id(task_id)
    
    if task is None:
        return jsonify({'error': 'Task not found'}), 404
    
    data = request.get_json()
    if not data or 'status' not in data:
        return jsonify({'error': 'Status is required'}), 400
    
    new_status = data['status']
    if new_status not in TaskStatus.ALL:
        return jsonify({'error': f'Invalid status. Must be one of: {TaskStatus.ALL}'}), 400
    
    old_status = task.status
    new_position = data.get('position')
    
    # Handle timer logic based on status change
    if old_status != new_status:
        # Moving FROM in_progress - stop timer
        if old_status == TaskStatus.IN_PROGRESS:
            TimeEntry.stop_timer(task_id)
        
        # Moving TO in_progress - start timer
        if new_status == TaskStatus.IN_PROGRESS:
            TimeEntry.start_timer(task_id)
    
    # Update task status and position
    task.update_status(new_status, new_position)
    
    task_dict = task.to_dict()
    task_dict['total_time'] = TimeEntry.get_total_time(task.id)
    task_dict['total_time_formatted'] = TimeEntry.format_duration(task_dict['total_time'])
    task_dict['active_timer_start'] = TimeEntry.get_active_start_time(task.id)
    task_dict['old_status'] = old_status
    
    return jsonify(task_dict)


@tasks_bp.route('/reorder', methods=['PUT'])
def reorder_tasks():
    """Reorder tasks within a column."""
    data = request.get_json()
    
    if not data or 'status' not in data or 'task_ids' not in data:
        return jsonify({'error': 'Status and task_ids are required'}), 400
    
    status = data['status']
    task_ids = data['task_ids']
    
    if status not in TaskStatus.ALL:
        return jsonify({'error': f'Invalid status. Must be one of: {TaskStatus.ALL}'}), 400
    
    if not isinstance(task_ids, list):
        return jsonify({'error': 'task_ids must be a list'}), 400
    
    Task.reorder_in_column(status, task_ids)
    
    return jsonify({'message': 'Tasks reordered successfully'})
