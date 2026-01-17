/**
 * Kanban Board Module
 * Handles drag-and-drop, task CRUD, and API interactions
 */

const Kanban = {
    // Store current tasks data
    tasks: {},
    
    // Currently selected task for details/edit
    currentTask: null,
    
    /**
     * Initialize the Kanban board
     */
    init() {
        this.setupEventListeners();
        this.loadTasks();
        this.setupDragAndDrop();
    },
    
    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Add task button
        document.getElementById('add-task-btn').addEventListener('click', () => {
            this.openTaskModal();
        });
        
        // Task form submission
        document.getElementById('task-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.saveTask();
        });
        
        // Cancel button
        document.getElementById('cancel-btn').addEventListener('click', () => {
            this.closeModal('task-modal');
        });
        
        // Modal close buttons
        document.querySelectorAll('.modal-close').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const modal = e.target.closest('.modal');
                this.closeModal(modal.id);
            });
        });
        
        // Close modal on backdrop click
        document.querySelectorAll('.modal').forEach(modal => {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    this.closeModal(modal.id);
                }
            });
        });
        
        // Edit button in details modal
        document.getElementById('edit-task-btn').addEventListener('click', () => {
            this.closeModal('details-modal');
            this.openTaskModal(this.currentTask);
        });
        
        // Delete button in details modal
        document.getElementById('delete-task-btn').addEventListener('click', () => {
            this.closeModal('details-modal');
            this.openConfirmModal();
        });
        
        // Confirm delete
        document.getElementById('confirm-delete-btn').addEventListener('click', () => {
            this.deleteTask(this.currentTask.id);
            this.closeModal('confirm-modal');
        });
        
        // Cancel delete
        document.getElementById('confirm-cancel-btn').addEventListener('click', () => {
            this.closeModal('confirm-modal');
        });
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                document.querySelectorAll('.modal:not(.hidden)').forEach(modal => {
                    this.closeModal(modal.id);
                });
            }
        });
    },
    
    /**
     * Setup drag and drop handlers
     */
    setupDragAndDrop() {
        const taskLists = document.querySelectorAll('.task-list');
        
        taskLists.forEach(list => {
            list.addEventListener('dragover', (e) => {
                e.preventDefault();
                list.classList.add('drag-over');
            });
            
            list.addEventListener('dragleave', (e) => {
                if (!list.contains(e.relatedTarget)) {
                    list.classList.remove('drag-over');
                }
            });
            
            list.addEventListener('drop', (e) => {
                e.preventDefault();
                list.classList.remove('drag-over');
                
                const taskId = e.dataTransfer.getData('text/plain');
                const newStatus = list.dataset.status;
                
                if (taskId) {
                    this.moveTask(parseInt(taskId), newStatus);
                }
            });
        });
    },
    
    /**
     * Load all tasks from API
     */
    async loadTasks() {
        try {
            const response = await fetch('/api/tasks');
            if (!response.ok) throw new Error('Failed to load tasks');
            
            this.tasks = await response.json();
            this.renderAllTasks();
            Timer.initializeActiveTimers(this.tasks);
        } catch (error) {
            console.error('Error loading tasks:', error);
            this.showToast('Failed to load tasks', 'error');
        }
    },
    
    /**
     * Render all tasks to their columns
     */
    renderAllTasks() {
        // Clear all task lists
        document.querySelectorAll('.task-list').forEach(list => {
            list.innerHTML = '';
        });
        
        // Render tasks for each status
        Object.entries(this.tasks).forEach(([status, tasks]) => {
            const list = document.querySelector(`.task-list[data-status="${status}"]`);
            if (list) {
                tasks.forEach(task => {
                    list.appendChild(this.createTaskCard(task));
                });
                
                // Update task count
                const countEl = document.querySelector(`.column[data-status="${status}"] .task-count`);
                if (countEl) {
                    countEl.textContent = tasks.length;
                }
            }
        });
    },
    
    /**
     * Create a task card element
     */
    createTaskCard(task) {
        const card = document.createElement('div');
        card.className = 'task-card';
        card.dataset.taskId = task.id;
        card.draggable = true;
        
        const hasActiveTimer = task.active_timer_start !== null;
        const timerClass = hasActiveTimer ? 'task-time active' : 'task-time';
        
        card.innerHTML = `
            <div class="task-title">${this.escapeHtml(task.title)}</div>
            ${task.description ? `<div class="task-description">${this.escapeHtml(task.description)}</div>` : ''}
            <div class="task-footer">
                <div class="${timerClass}">
                    ${hasActiveTimer ? '<span class="timer-indicator"><span class="pulse"></span></span>' : ''}
                    <span class="timer-display">${task.total_time_formatted || '00:00:00'}</span>
                </div>
                <div class="task-actions">
                    <button class="action-btn view-btn" title="View Details">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
                            <circle cx="12" cy="12" r="3"></circle>
                        </svg>
                    </button>
                </div>
            </div>
        `;
        
        // Drag start
        card.addEventListener('dragstart', (e) => {
            card.classList.add('dragging');
            e.dataTransfer.setData('text/plain', task.id);
            e.dataTransfer.effectAllowed = 'move';
        });
        
        // Drag end
        card.addEventListener('dragend', () => {
            card.classList.remove('dragging');
            document.querySelectorAll('.task-list').forEach(list => {
                list.classList.remove('drag-over');
            });
        });
        
        // View details
        card.querySelector('.view-btn').addEventListener('click', (e) => {
            e.stopPropagation();
            this.openDetailsModal(task);
        });
        
        // Double click to edit
        card.addEventListener('dblclick', () => {
            this.openTaskModal(task);
        });
        
        return card;
    },
    
    /**
     * Move task to a new status/column
     */
    async moveTask(taskId, newStatus) {
        try {
            const response = await fetch(`/api/tasks/${taskId}/status`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ status: newStatus })
            });
            
            if (!response.ok) throw new Error('Failed to move task');
            
            const updatedTask = await response.json();
            
            // Handle timer updates based on status change
            if (updatedTask.old_status === 'in_progress' && newStatus !== 'in_progress') {
                // Timer stopped
                Timer.stopLiveUpdate(taskId);
            } else if (updatedTask.old_status !== 'in_progress' && newStatus === 'in_progress') {
                // Timer started
                const baseSeconds = updatedTask.total_time - Timer.getElapsedSeconds(updatedTask.active_timer_start);
                Timer.startLiveUpdate(taskId, updatedTask.active_timer_start, Math.max(0, baseSeconds));
            }
            
            // Reload tasks to ensure consistent state
            await this.loadTasks();
            
            this.showToast(`Task moved to ${this.getStatusDisplayName(newStatus)}`, 'success');
        } catch (error) {
            console.error('Error moving task:', error);
            this.showToast('Failed to move task', 'error');
            // Reload to restore correct state
            await this.loadTasks();
        }
    },
    
    /**
     * Open task modal for creating/editing
     */
    openTaskModal(task = null) {
        const modal = document.getElementById('task-modal');
        const title = document.getElementById('modal-title');
        const taskId = document.getElementById('task-id');
        const taskTitle = document.getElementById('task-title');
        const taskDescription = document.getElementById('task-description');
        
        if (task) {
            title.textContent = 'Edit Task';
            taskId.value = task.id;
            taskTitle.value = task.title;
            taskDescription.value = task.description || '';
        } else {
            title.textContent = 'Add New Task';
            taskId.value = '';
            taskTitle.value = '';
            taskDescription.value = '';
        }
        
        modal.classList.remove('hidden');
        taskTitle.focus();
    },
    
    /**
     * Save task (create or update)
     */
    async saveTask() {
        const taskId = document.getElementById('task-id').value;
        const title = document.getElementById('task-title').value.trim();
        const description = document.getElementById('task-description').value.trim();
        
        if (!title) {
            this.showToast('Title is required', 'error');
            return;
        }
        
        try {
            let response;
            
            if (taskId) {
                // Update existing task
                response = await fetch(`/api/tasks/${taskId}`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ title, description })
                });
            } else {
                // Create new task
                response = await fetch('/api/tasks', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ title, description, status: 'todo' })
                });
            }
            
            if (!response.ok) throw new Error('Failed to save task');
            
            this.closeModal('task-modal');
            await this.loadTasks();
            this.showToast(taskId ? 'Task updated' : 'Task created', 'success');
        } catch (error) {
            console.error('Error saving task:', error);
            this.showToast('Failed to save task', 'error');
        }
    },
    
    /**
     * Delete a task
     */
    async deleteTask(taskId) {
        try {
            const response = await fetch(`/api/tasks/${taskId}`, {
                method: 'DELETE'
            });
            
            if (!response.ok) throw new Error('Failed to delete task');
            
            Timer.stopLiveUpdate(taskId);
            await this.loadTasks();
            this.showToast('Task deleted', 'success');
        } catch (error) {
            console.error('Error deleting task:', error);
            this.showToast('Failed to delete task', 'error');
        }
    },
    
    /**
     * Open task details modal
     */
    async openDetailsModal(task) {
        this.currentTask = task;
        
        const modal = document.getElementById('details-modal');
        document.getElementById('details-title').textContent = task.title;
        document.getElementById('details-description').textContent = task.description || 'No description';
        document.getElementById('details-total-time').textContent = task.total_time_formatted || '00:00:00';
        
        // Load time entries
        try {
            const response = await fetch(`/api/timer/${task.id}/entries`);
            if (response.ok) {
                const data = await response.json();
                this.renderTimeEntries(data.entries);
            }
        } catch (error) {
            console.error('Error loading time entries:', error);
        }
        
        modal.classList.remove('hidden');
    },
    
    /**
     * Render time entries in details modal
     */
    renderTimeEntries(entries) {
        const container = document.getElementById('time-entries-list');
        
        if (!entries || entries.length === 0) {
            container.innerHTML = '<div class="empty-state">No time entries yet</div>';
            return;
        }
        
        container.innerHTML = entries.map(entry => {
            const startDate = new Date(entry.start_time);
            const isActive = entry.end_time === null;
            const duration = isActive 
                ? Timer.formatDuration(Timer.getElapsedSeconds(entry.start_time))
                : Timer.formatDuration(entry.duration);
            
            return `
                <div class="time-entry ${isActive ? 'active' : ''}">
                    <span class="entry-date">${startDate.toLocaleString()}</span>
                    <span class="entry-duration">${duration}${isActive ? ' (running)' : ''}</span>
                </div>
            `;
        }).join('');
    },
    
    /**
     * Open confirmation modal
     */
    openConfirmModal() {
        document.getElementById('confirm-modal').classList.remove('hidden');
    },
    
    /**
     * Close a modal by ID
     */
    closeModal(modalId) {
        document.getElementById(modalId).classList.add('hidden');
    },
    
    /**
     * Show toast notification
     */
    showToast(message, type = 'info') {
        let container = document.querySelector('.toast-container');
        if (!container) {
            container = document.createElement('div');
            container.className = 'toast-container';
            document.body.appendChild(container);
        }
        
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.textContent = message;
        container.appendChild(toast);
        
        setTimeout(() => {
            toast.remove();
        }, 3000);
    },
    
    /**
     * Get display name for status
     */
    getStatusDisplayName(status) {
        const names = {
            'todo': 'To Do',
            'in_progress': 'In Progress',
            'waiting': 'Waiting',
            'done': 'Done'
        };
        return names[status] || status;
    },
    
    /**
     * Escape HTML to prevent XSS
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
};

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    Kanban.init();
});
