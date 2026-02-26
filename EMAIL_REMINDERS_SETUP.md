# 📧 Email Reminder Setup Guide

## What's New?

Automated email reminders for upcoming task deadlines! Users receive beautiful HTML emails when tasks are due soon.

## Features

✅ **Automated Reminders** - Sends emails for tasks due in 24 hours  
✅ **Beautiful HTML Emails** - Professional design with task details  
✅ **Smart Scheduling** - Checks every 6 hours + daily at 9 AM  
✅ **Grouped by User** - One email per user with all their tasks  
✅ **Priority Color Coding** - Visual priority indicators  

## Setup Instructions

### Step 1: Install Dependencies
```bash
pip install schedule
```

### Step 2: Configure Gmail App Password

**Why App Password?**
Gmail requires an "App Password" for security (not your regular password).

**Get App Password:**
1. Go to: https://myaccount.google.com/apppasswords
2. Sign in to your Gmail account
3. Select "Mail" and "Windows Computer"
4. Click "Generate"
5. Copy the 16-character password (e.g., `abcd efgh ijkl mnop`)

### Step 3: Update Email Configuration

Edit `email_reminders.py`:

```python
SENDER_EMAIL = "your-email@gmail.com"  # Your Gmail address
SENDER_PASSWORD = "abcd efgh ijkl mnop"  # Your App Password (no spaces)
```

**Example:**
```python
SENDER_EMAIL = "priorityiq@gmail.com"
SENDER_PASSWORD = "abcdefghijklmnop"
```

### Step 4: Test Email Service

```bash
python email_reminders.py
```

This will send test emails for any tasks due in the next 24 hours.

### Step 5: Start Flask

```bash
python app.py
```

You'll see: `📧 Email reminder service started!`

## How It Works

### Automatic Checks:
- **Every 6 hours** - Continuous monitoring
- **Daily at 9 AM** - Morning reminder
- **On Flask startup** - Initial check

### Email Triggers:
- Tasks due **today**
- Tasks due **tomorrow**
- Tasks **overdue**

### Email Content:
```
Subject: ⚠️ PriorityIQ: 3 Task(s) Due Soon!

Hi John,

You have 3 task(s) due soon:

📋 Complete Project Report
📅 Due: February 12, 2026
⚡ Priority: High

📋 Review Code Changes
📅 Due: February 12, 2026
⚡ Priority: Medium

[View Tasks Button]
```

## Customization

### Change Email Schedule

Edit `email_reminders.py`:

```python
# Check every 3 hours instead of 6
schedule.every(3).hours.do(check_and_send_reminders)

# Check at 8 AM and 6 PM
schedule.every().day.at("08:00").do(check_and_send_reminders)
schedule.every().day.at("18:00").do(check_and_send_reminders)
```

### Change Deadline Window

```python
# Send reminders for tasks due in next 3 days
AND t.deadline BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 3 DAY)
```

### Customize Email Template

Edit the HTML in `send_email()` function to match your branding.

## Troubleshooting

### Error: "Authentication failed"
**Solution:** 
- Use App Password, not regular password
- Enable "Less secure app access" (not recommended)
- Check Gmail account settings

### Error: "SMTPException"
**Solution:**
- Check internet connection
- Verify SMTP server and port
- Try port 465 with SSL instead of 587

### Emails Not Sending
**Solution:**
- Check if tasks exist with deadlines in next 24 hours
- Verify email configuration
- Check console for error messages
- Test with: `python email_reminders.py`

### Gmail Blocking Emails
**Solution:**
- Use App Password (required)
- Enable 2-factor authentication on Gmail
- Check Gmail security settings

## Alternative Email Providers

### Outlook/Hotmail:
```python
SMTP_SERVER = "smtp-mail.outlook.com"
SMTP_PORT = 587
```

### Yahoo:
```python
SMTP_SERVER = "smtp.mail.yahoo.com"
SMTP_PORT = 587
```

### Custom SMTP:
```python
SMTP_SERVER = "mail.yourdomain.com"
SMTP_PORT = 587
```

## Production Deployment

### Use Environment Variables:

Add to `.env`:
```
EMAIL_SENDER=your-email@gmail.com
EMAIL_PASSWORD=your-app-password
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
```

Update `email_reminders.py`:
```python
import os
from dotenv import load_dotenv

load_dotenv()

SENDER_EMAIL = os.getenv("EMAIL_SENDER")
SENDER_PASSWORD = os.getenv("EMAIL_PASSWORD")
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
```

## Disable Email Reminders

If you don't want email reminders:

1. Don't install `schedule` package
2. Flask will show: "Email reminders disabled (missing dependencies)"
3. App works normally without emails

## Testing

### Test Single Email:
```python
from email_reminders import send_email

send_email(
    "test@example.com",
    "Test Subject",
    "<h1>Test Email</h1><p>This is a test.</p>"
)
```

### Test Reminder Check:
```python
from email_reminders import check_and_send_reminders

check_and_send_reminders()
```

## Benefits

🎯 **Never Miss Deadlines** - Automatic reminders  
📧 **Professional Emails** - Beautiful HTML design  
⏰ **Smart Scheduling** - Checks multiple times daily  
🎨 **Priority Coding** - Visual priority indicators  
📊 **Grouped Notifications** - One email per user  
🔄 **Background Service** - Runs automatically  

## Total Features: 48

Added email reminder system! 🎉

---

**Your tasks will now send email reminders automatically!** 📧✨
