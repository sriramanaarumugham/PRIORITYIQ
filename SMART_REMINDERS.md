# Smart Reminder System 🎯

## Overview
PriorityIQ now features an **intelligent reminder system** that alerts you **before** the deadline based on the estimated time needed to complete each task.

## How It Works

### Traditional Reminders (Old Way)
- Alert 24 hours before deadline
- Same reminder for all tasks regardless of complexity
- Often too late to start working

### Smart Reminders (New Way) ⚡
- Calculates when you need to **START** working
- Based on **estimated hours** required
- Includes 2-hour buffer for safety

## Examples

### Example 1: Long Task
- **Task**: Write research paper
- **Estimated Time**: 8 hours
- **Deadline**: Friday 5 PM
- **Smart Alert**: Thursday 9 AM (8 hours + 2 hour buffer before deadline)
- **Message**: "START NOW! Need 8h, only 10h left"

### Example 2: Quick Task
- **Task**: Reply to email
- **Estimated Time**: 0.5 hours
- **Deadline**: Tomorrow 3 PM
- **Smart Alert**: Tomorrow 12:30 PM (0.5 hours + 2 hour buffer)
- **Message**: "URGENT! Start soon - 2.5h until deadline"

### Example 3: Already Late
- **Task**: Submit report
- **Estimated Time**: 5 hours
- **Deadline**: Today 2 PM (current time: 12 PM)
- **Smart Alert**: NOW (only 2 hours left, need 5 hours)
- **Message**: "START NOW! Need 5h, only 2h left"

## Alert Types

### 🔴 Critical (Red)
- Time remaining ≤ Estimated time needed
- **Action**: Start immediately!
- **Sound**: 3 urgent beeps
- **Email**: Sent immediately

### 🟠 High (Orange)
- Time remaining ≤ Estimated time + 2 hours
- **Action**: Start very soon
- **Sound**: 1 alert beep
- **Email**: Sent in next check cycle

### 🟡 Medium (Yellow)
- Due tomorrow or in 2-3 days
- **Action**: Plan to start soon
- **Sound**: Soft notification
- **Email**: Daily reminder

### ⚫ Overdue (Black)
- Past deadline
- **Action**: Complete ASAP!
- **Sound**: 3 urgent beeps
- **Email**: Immediate alert

## Notification Channels

### 1. Real-Time Browser Alerts
- Checks every 30 minutes
- Visual notification slides in from right
- Sound effects for urgent tasks
- Auto-dismisses after 10 seconds

### 2. Email Reminders
- Checks every 6 hours + daily at 9 AM
- HTML formatted with color-coded priorities
- Shows hours remaining vs. hours needed
- Grouped by user (multi-user support)

## Configuration

### Email Setup (.env file)
```env
SENDER_EMAIL=your_email@gmail.com
SENDER_PASSWORD=your_app_password
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
```

### Reminder Schedule
- **Real-time alerts**: Every 30 minutes
- **Email reminders**: Every 6 hours + 9 AM daily
- **Buffer time**: 2 hours (configurable in code)

## Benefits

✅ **Never miss deadlines** - Alerts before it's too late  
✅ **Smart prioritization** - Focus on urgent tasks first  
✅ **Time management** - Know when to start working  
✅ **Stress reduction** - No last-minute panic  
✅ **Productivity boost** - Better planning and execution  

## Technical Details

### Algorithm
```python
hours_until_deadline = (deadline - now).total_seconds() / 3600
est_hours = task.est_hours
buffer = 2  # hours

if hours_until_deadline <= (est_hours + buffer):
    send_alert("START NOW!")
```

### Database Fields Used
- `deadline` - Task due date
- `est_hours` - Estimated completion time
- `status` - Task status (skip if Completed)
- `priority_level` - High/Medium/Low

## User Experience

### Before Smart Reminders
❌ "Task due tomorrow" - Too vague  
❌ Same alert for 1-hour and 10-hour tasks  
❌ Often start too late  

### After Smart Reminders
✅ "Need 8h, only 10h left - START NOW!"  
✅ Personalized based on task complexity  
✅ Start at the right time  

## Future Enhancements

- [ ] Machine learning to predict actual completion time
- [ ] Adjust buffer based on user's past performance
- [ ] SMS/WhatsApp notifications
- [ ] Calendar integration (Google Calendar, Outlook)
- [ ] Snooze functionality for reminders
- [ ] Custom reminder schedules per task

## Troubleshooting

### Not receiving email reminders?
1. Check `.env` file has correct email credentials
2. Enable "Less secure app access" or use App Password for Gmail
3. Check spam/junk folder
4. Verify Flask app is running

### Browser alerts not showing?
1. Allow notifications in browser settings
2. Check if deadline-alerts.js is loaded
3. Ensure tasks have `est_hours` field populated
4. Open browser console for error messages

## Credits

Smart Reminder System developed for PriorityIQ v2.0  
Feature requested by users for better time management  
Implemented: 2024
