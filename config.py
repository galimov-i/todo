"""Configuration settings for the Kanban application."""
import os

# Base directory of the project
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Database configuration
DATABASE_PATH = os.path.join(BASE_DIR, 'kanban.db')

# Flask configuration
class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    DATABASE = DATABASE_PATH
    DEBUG = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'

# Task status constants
class TaskStatus:
    TODO = 'todo'
    IN_PROGRESS = 'in_progress'
    WAITING = 'waiting'
    DONE = 'done'
    
    ALL = [TODO, IN_PROGRESS, WAITING, DONE]
    
    # Display names for UI
    DISPLAY_NAMES = {
        TODO: 'To Do',
        IN_PROGRESS: 'In Progress',
        WAITING: 'Waiting',
        DONE: 'Done'
    }
