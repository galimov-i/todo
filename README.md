# Kanban Board with Time Tracking

A minimal Trello-like Kanban board application with automatic time tracking functionality. Built with Python, Flask, SQLite, and vanilla JavaScript.

## Overview

This application provides a simple yet powerful way to manage tasks using the Kanban methodology while automatically tracking time spent on each task. When you move a task to "In Progress", the timer starts automatically. When you move it to any other column, the timer pauses and saves the elapsed time.

## Features

- **Four Workflow Columns**: To Do, In Progress, Waiting, Done
- **Drag-and-Drop**: Move tasks between columns using native HTML5 drag and drop
- **Automatic Time Tracking**: Timer starts when task moves to "In Progress"
- **Timer Auto-Pause**: Timer stops when task moves to other columns
- **Persistent Data**: All data stored in SQLite database
- **Real-Time Display**: Live timer updates on active tasks
- **Time History**: View detailed time entries per task
- **Responsive Design**: Works on desktop and mobile devices
- **No External Dependencies**: Uses vanilla JavaScript, no frontend frameworks needed

## Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | Flask 3.0+ (Python) |
| Database | SQLite (embedded, no server needed) |
| Frontend | HTML5, CSS3, Vanilla JavaScript |
| Drag & Drop | Native HTML5 Drag and Drop API |
| Templating | Jinja2 (built into Flask) |
| API | RESTful JSON endpoints |

## Prerequisites

- Python 3.9 or higher (includes SQLite3)
- pip (Python package manager)

**Note:** SQLite is included with Python - no separate database installation needed!

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd kanban-tracker
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Linux/macOS:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Initialize Database

```bash
python -c "from database.db import init_db; init_db()"
```

Optionally, seed with sample data:

```bash
python -c "from database.db import init_db, seed_db; init_db(); seed_db()"
```

### 5. Run the Application

```bash
python app.py
```

The application will be available at: http://localhost:5000

## Project Structure

```
kanban-tracker/
├── README.md                 # This file (English)
├── README_RUS.md             # Russian documentation
├── app.py                    # Main Flask application
├── config.py                 # Configuration settings
├── requirements.txt          # Python dependencies
├── .gitignore                # Git ignore file
├── kanban.db                 # SQLite database (auto-created)
├── database/
│   ├── __init__.py
│   ├── db.py                 # DB initialization and connection
│   └── schema.sql            # SQL schema
├── models/
│   ├── __init__.py
│   ├── task.py               # Task model
│   └── time_entry.py         # Time entry model
├── routes/
│   ├── __init__.py
│   ├── tasks.py              # Task CRUD endpoints
│   └── timer.py              # Timer management endpoints
├── static/
│   ├── css/
│   │   └── style.css         # Application styles
│   └── js/
│       ├── kanban.js         # Drag-and-drop logic
│       └── timer.js          # Timer logic
└── templates/
    └── index.html            # Main Kanban board page
```

## API Reference

### Tasks

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/tasks` | Get all tasks grouped by status |
| GET | `/api/tasks/{id}` | Get single task with time entries |
| POST | `/api/tasks` | Create new task |
| PUT | `/api/tasks/{id}` | Update task title/description |
| PUT | `/api/tasks/{id}/status` | Move task to new column |
| DELETE | `/api/tasks/{id}` | Delete task |
| PUT | `/api/tasks/reorder` | Reorder tasks within column |

### Timer

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/timer/{task_id}/start` | Manually start timer |
| POST | `/api/timer/{task_id}/stop` | Manually stop timer |
| GET | `/api/timer/{task_id}/status` | Get timer status |
| GET | `/api/timer/{task_id}/entries` | Get time entries for task |
| GET | `/api/timer/active` | Get all active timers |

### Request/Response Examples

**Create Task:**
```bash
curl -X POST http://localhost:5000/api/tasks \
  -H "Content-Type: application/json" \
  -d '{"title": "New Task", "description": "Task description"}'
```

**Move Task to In Progress (starts timer):**
```bash
curl -X PUT http://localhost:5000/api/tasks/1/status \
  -H "Content-Type: application/json" \
  -d '{"status": "in_progress"}'
```

## Usage Guide

### Creating Tasks

1. Click the **"+ Add Task"** button in the header
2. Enter a title (required) and description (optional)
3. Click **"Save Task"**
4. The task appears in the "To Do" column

### Moving Tasks

1. **Drag and drop**: Click and hold a task card, drag to desired column
2. Timer automatically starts when dropped in "In Progress"
3. Timer automatically stops when moved to other columns

### Viewing Task Details

1. Click the **eye icon** on a task card
2. View description, total time, and time entry history
3. Use **Edit** or **Delete** buttons as needed

### Editing Tasks

- **Quick edit**: Double-click any task card
- **From details**: Open task details and click "Edit"

### Time Tracking

- **Automatic**: Timer starts/stops on column changes
- **View time**: Shown on each task card in HH:MM:SS format
- **Active indicator**: Green pulsing dot shows running timer
- **History**: View all time entries in task details

## Database Schema

### Tasks Table
```sql
CREATE TABLE tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'todo',
    position INTEGER NOT NULL DEFAULT 0,
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL
);
```

### Time Entries Table
```sql
CREATE TABLE time_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL,
    start_time INTEGER NOT NULL,
    end_time INTEGER,
    duration INTEGER,
    created_at INTEGER NOT NULL,
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
);
```

## Troubleshooting

### Database Issues

**Problem:** "Database not found" error
```bash
# Reinitialize the database
python -c "from database.db import init_db; init_db()"
```

**Problem:** Corrupted database
```bash
# Delete and recreate
rm kanban.db
python -c "from database.db import init_db; init_db()"
```

### Timer Issues

**Problem:** Timer not updating in real-time
- Ensure JavaScript is enabled in your browser
- Check browser console for errors
- Refresh the page

**Problem:** Time not saved
- Timer saves when task moves from "In Progress" to another column
- Ensure the API call completes successfully

### Connection Issues

**Problem:** Cannot access http://localhost:5000
- Ensure Flask server is running
- Check if port 5000 is available
- Try: `python app.py` and watch for errors

## Development

### Running in Debug Mode

```bash
FLASK_DEBUG=true python app.py
```

### Running Tests

```bash
python -c "
from app import app
from database.db import init_db

with app.test_client() as client:
    # Test health endpoint
    resp = client.get('/api/health')
    assert resp.status_code == 200
    print('Health check: OK')
    
    # Test tasks endpoint
    resp = client.get('/api/tasks')
    assert resp.status_code == 200
    print('Tasks endpoint: OK')
"
```

## License

This project is open source and available under the MIT License.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## Acknowledgments

- Built with [Flask](https://flask.palletsprojects.com/)
- Uses [SQLite](https://www.sqlite.org/) for data persistence
- Inspired by [Trello](https://trello.com/) and other Kanban tools
