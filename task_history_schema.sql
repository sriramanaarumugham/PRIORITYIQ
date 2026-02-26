-- Task History Table Schema
-- Run this in MySQL Workbench to add task history tracking

USE priorityiq;

CREATE TABLE IF NOT EXISTS task_history (
    history_id INT AUTO_INCREMENT PRIMARY KEY,
    task_id INT NOT NULL,
    user_id INT NOT NULL,
    action_type VARCHAR(50) NOT NULL,
    field_changed VARCHAR(100),
    old_value TEXT,
    new_value TEXT,
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES tasks(task_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    INDEX idx_task_id (task_id),
    INDEX idx_user_id (user_id),
    INDEX idx_changed_at (changed_at)
);

-- Action types:
-- 'CREATED' - Task created
-- 'STATUS_CHANGED' - Status updated
-- 'PRIORITY_CHANGED' - Priority updated
-- 'DEADLINE_CHANGED' - Deadline modified
-- 'UPDATED' - General update
-- 'DELETED' - Task deleted
-- 'COMPLETED' - Task marked as completed
-- 'REOPENED' - Completed task reopened
