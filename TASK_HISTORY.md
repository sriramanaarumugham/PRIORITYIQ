# Task History Feature 📜

## Overview
Track every change made to your tasks with a complete audit trail.

## What Gets Tracked

### 1. Task Created
- When: New task is added
- Info: Task title and initial details

### 2. Status Changed
- When: Task moves between Pending/In Progress/Completed
- Info: Old status → New status

### 3. Task Completed
- When: Task marked as completed
- Info: Completion timestamp
- Bonus: +50 XP points awarded

### 4. Priority Changed
- When: Priority updated (High/Medium/Low)
- Info: Old priority → New priority

### 5. Deadline Changed
- When: Due date is modified
- Info: Old deadline → New deadline

### 6. Task Updated
- When: Other fields modified (title, description, etc.)
- Info: General update logged

### 7. Task Deleted
- When: Task is removed
- Info: Task title before deletion

## API Endpoints

### Get Task History
```
GET /api/history/task/<task_id>
```
Returns complete history for a specific task.

### Get Recent Activity
```
GET /api/history/recent?limit=20
```
Returns recent activity across all tasks.

### Get Statistics
```
GET /api/history/stats
```
Returns activity statistics and trends.

## Database Schema

```sql
CREATE TABLE task_history (
    history_id INT AUTO_INCREMENT PRIMARY KEY,
    task_id INT NOT NULL,
    user_id INT NOT NULL,
    action_type VARCHAR(50) NOT NULL,
    field_changed VARCHAR(100),
    old_value TEXT,
    new_value TEXT,
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Setup Instructions

1. Run SQL schema:
```bash
mysql -u root -p priorityiq < task_history_schema.sql
```

2. Restart Flask app:
```bash
python app.py
```

3. Access history page:
```
http://127.0.0.1:5000/history
```

## Features

✅ Complete audit trail
✅ Timeline visualization
✅ Activity statistics
✅ Color-coded action types
✅ Automatic logging
✅ No manual intervention needed

## Benefits

- **Accountability**: Know who changed what and when
- **Debugging**: Track down when issues occurred
- **Analytics**: Understand task lifecycle patterns
- **Compliance**: Maintain audit logs for reporting

## Total Features: 50+

Your PriorityIQ now has 50+ features including task history tracking!
