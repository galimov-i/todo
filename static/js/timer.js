/**
 * Timer module for Kanban Board
 * Handles real-time timer display and updates
 */

const Timer = {
    // Store active timer intervals
    intervals: {},
    
    /**
     * Format seconds to HH:MM:SS
     */
    formatDuration(seconds) {
        if (seconds === null || seconds === undefined || seconds < 0) {
            return '00:00:00';
        }
        
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = Math.floor(seconds % 60);
        
        return [hours, minutes, secs]
            .map(v => v.toString().padStart(2, '0'))
            .join(':');
    },
    
    /**
     * Calculate elapsed time from start timestamp
     */
    getElapsedSeconds(startTimeMs) {
        const now = Date.now();
        return Math.floor((now - startTimeMs) / 1000);
    },
    
    /**
     * Start a live timer update for a task
     */
    startLiveUpdate(taskId, startTimeMs, baseSeconds = 0) {
        // Clear any existing interval for this task
        this.stopLiveUpdate(taskId);
        
        const updateTimer = () => {
            const elapsed = this.getElapsedSeconds(startTimeMs);
            const total = baseSeconds + elapsed;
            const element = document.querySelector(`[data-task-id="${taskId}"] .timer-display`);
            
            if (element) {
                element.textContent = this.formatDuration(total);
                element.classList.add('active');
            }
        };
        
        // Update immediately, then every second
        updateTimer();
        this.intervals[taskId] = setInterval(updateTimer, 1000);
    },
    
    /**
     * Stop live timer update for a task
     */
    stopLiveUpdate(taskId) {
        if (this.intervals[taskId]) {
            clearInterval(this.intervals[taskId]);
            delete this.intervals[taskId];
        }
        
        const element = document.querySelector(`[data-task-id="${taskId}"] .timer-display`);
        if (element) {
            element.classList.remove('active');
        }
    },
    
    /**
     * Stop all live timer updates
     */
    stopAllLiveUpdates() {
        Object.keys(this.intervals).forEach(taskId => {
            this.stopLiveUpdate(taskId);
        });
    },
    
    /**
     * Update timer display with static value
     */
    updateDisplay(taskId, formattedTime, isActive = false) {
        const element = document.querySelector(`[data-task-id="${taskId}"] .timer-display`);
        if (element) {
            element.textContent = formattedTime;
            if (isActive) {
                element.classList.add('active');
            } else {
                element.classList.remove('active');
            }
        }
    },
    
    /**
     * Initialize timers for all tasks with active timers
     */
    initializeActiveTimers(tasks) {
        Object.values(tasks).flat().forEach(task => {
            if (task.active_timer_start) {
                // Calculate base seconds (completed time entries)
                const elapsed = this.getElapsedSeconds(task.active_timer_start);
                const baseSeconds = (task.total_time || 0) - elapsed;
                this.startLiveUpdate(task.id, task.active_timer_start, Math.max(0, baseSeconds));
            }
        });
    }
};

// Export for use in kanban.js
window.Timer = Timer;
