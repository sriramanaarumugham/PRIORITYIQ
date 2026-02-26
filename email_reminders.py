import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from db_connection import get_db_connection
import schedule
import time
import threading
import os
from dotenv import load_dotenv

load_dotenv()

# Email configuration from environment variables
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD", "")

def send_email(to_email, subject, body):
    """Send email notification"""
    if not SENDER_EMAIL or not SENDER_PASSWORD:
        print("⚠️ Email not configured. Add SENDER_EMAIL and SENDER_PASSWORD to .env file")
        return False
    
    try:
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = to_email
        msg['Subject'] = subject
        
        msg.attach(MIMEText(body, 'html'))
        
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)
        server.quit()
        
        print(f"✅ Email sent to {to_email}")
        return True
    except Exception as e:
        print(f"❌ Email failed: {e}")
        return False

def check_and_send_reminders():
    """Check for upcoming deadlines and send smart reminders based on estimated hours"""
    try:
        conn = get_db_connection()
        if not conn:
            return
        
        cursor = conn.cursor(dictionary=True)
        
        # Get all incomplete tasks
        query = """
            SELECT t.*, u.email, u.name 
            FROM tasks t 
            JOIN users u ON t.user_id = u.user_id 
            WHERE t.status != 'Completed' 
            AND t.deadline >= CURDATE()
        """
        
        cursor.execute(query)
        tasks = cursor.fetchall()
        
        # Filter tasks that need reminders based on estimated hours
        now = datetime.now()
        tasks_to_remind = []
        
        for task in tasks:
            deadline = datetime.combine(task['deadline'], datetime.max.time())
            hours_until_deadline = (deadline - now).total_seconds() / 3600
            est_hours = task.get('est_hours', 0) or 0
            
            # Alert if time remaining <= estimated time needed (with 2-hour buffer)
            if hours_until_deadline <= (est_hours + 2):
                task['hours_left'] = int(hours_until_deadline)
                task['needs_hours'] = est_hours
                tasks_to_remind.append(task)
        
        # Group tasks by user
        user_tasks = {}
        for task in tasks_to_remind:
            email = task['email']
            if email not in user_tasks:
                user_tasks[email] = {
                    'name': task['name'],
                    'tasks': []
                }
            user_tasks[email]['tasks'].append(task)
        
        # Send emails
        for email, data in user_tasks.items():
            subject = f"⏰ PriorityIQ: {len(data['tasks'])} Task(s) Need Your Attention NOW!"
            
            body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; padding: 20px; background: #f5f5f5;">
                <div style="max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                    <h2 style="color: #e74c3c; margin-top: 0;">⏰ Smart Deadline Alert</h2>
                    <p>Hi <strong>{data['name']}</strong>,</p>
                    <p>Based on estimated completion time, you need to <strong style="color: #e74c3c;">START WORKING</strong> on these tasks now:</p>
                    
                    <div style="background: #f9f9f9; padding: 15px; border-radius: 8px; margin: 20px 0;">
            """
            
            for task in data['tasks']:
                deadline = task['deadline'].strftime('%B %d, %Y')
                priority = task.get('priority_level', 'Medium')
                priority_color = {'High': '#e74c3c', 'Medium': '#f39c12', 'Low': '#2ecc71'}.get(priority, '#999')
                hours_left = task.get('hours_left', 0)
                needs_hours = task.get('needs_hours', 0)
                
                urgency_msg = ""
                if hours_left <= needs_hours:
                    urgency_msg = f"<br>⏰ <strong style='color: #e74c3c;'>START NOW!</strong> You need {needs_hours}h but only have {hours_left}h left!"
                
                body += f"""
                    <div style="margin-bottom: 15px; padding: 10px; background: white; border-radius: 5px; border-left: 4px solid {priority_color};">
                        <h3 style="margin: 0 0 5px 0; color: #333;">{task['title']}</h3>
                        <p style="margin: 5px 0; color: #666; font-size: 14px;">
                            📅 Due: {deadline}<br>
                            ⚡ Priority: <span style="color: {priority_color}; font-weight: bold;">{priority}</span><br>
                            ⏱️ Estimated Time: {needs_hours} hours{urgency_msg}
                        </p>
                    </div>
                """
            
            body += f"""
                    </div>
                    
                    <p style="margin-top: 20px;">
                        <a href="http://127.0.0.1:5000" style="background: #4b5cff; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block;">
                            View Tasks
                        </a>
                    </p>
                    
                    <p style="color: #999; font-size: 12px; margin-top: 30px;">
                        This is a smart reminder from PriorityIQ based on your task's estimated completion time.<br>
                        Start working now to meet your deadline! 🚀
                    </p>
                </div>
            </body>
            </html>
            """
            
            send_email(email, subject, body)
        
        cursor.close()
        conn.close()
        
        print(f"✅ Checked reminders at {datetime.now()}")
        
    except Exception as e:
        print(f"❌ Error checking reminders: {e}")

def start_email_scheduler():
    """Start background scheduler for email reminders"""
    # Check every day at 9 AM
    schedule.every().day.at("09:00").do(check_and_send_reminders)
    
    # Also check every 6 hours
    schedule.every(6).hours.do(check_and_send_reminders)
    
    def run_scheduler():
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    
    # Run in background thread
    thread = threading.Thread(target=run_scheduler, daemon=True)
    thread.start()
    print("📧 Email reminder service started!")

if __name__ == "__main__":
    # Test email
    check_and_send_reminders()
