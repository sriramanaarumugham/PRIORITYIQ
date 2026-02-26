from flask import Blueprint, request, jsonify, session
from db_connection import get_db_connection
import re
from datetime import datetime, timedelta

chatbot_bp = Blueprint("chatbot_bp", __name__)

def require_login():
    return 'user_id' in session

class TaskAssistant:
    def __init__(self, user_id):
        self.user_id = user_id
        
    def get_tasks_data(self):
        """Fetch user's tasks for context"""
        conn = get_db_connection()
        if not conn:
            return []
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM tasks WHERE user_id=%s ORDER BY created_at DESC LIMIT 50", (self.user_id,))
        tasks = cursor.fetchall()
        cursor.close()
        conn.close()
        return tasks
    
    def analyze_intent(self, message):
        """Determine user's intent from message"""
        message = message.lower()
        
        # Task creation intents
        if any(word in message for word in ['add', 'create', 'new task', 'make task']):
            return 'create_task'
        
        # Query intents
        if any(word in message for word in ['how many', 'count', 'total']):
            return 'count_tasks'
        
        if any(word in message for word in ['overdue', 'late', 'missed']):
            return 'overdue_tasks'
        
        if any(word in message for word in ['today', 'due today']):
            return 'today_tasks'
        
        if any(word in message for word in ['high priority', 'urgent', 'important']):
            return 'high_priority'
        
        if any(word in message for word in ['completed', 'done', 'finished']):
            return 'completed_tasks'
        
        if any(word in message for word in ['pending', 'todo', 'to do']):
            return 'pending_tasks'
        
        # Recommendation intents
        if any(word in message for word in ['what should', 'recommend', 'suggest', 'next task']):
            return 'recommend_task'
        
        # Analytics intents
        if any(word in message for word in ['productivity', 'performance', 'stats', 'analytics']):
            return 'analytics'
        
        # Help intent
        if any(word in message for word in ['help', 'what can you', 'commands']):
            return 'help'
        
        return 'general'
    
    def extract_task_info(self, message):
        """Extract task details from natural language"""
        task_info = {
            'title': None,
            'urgency': 3,
            'deadline': None
        }
        
        # Extract title (text between quotes or after "task:")
        title_match = re.search(r'"([^"]+)"', message)
        if title_match:
            task_info['title'] = title_match.group(1)
        elif 'task:' in message.lower():
            task_info['title'] = message.split('task:', 1)[1].strip()
        
        # Extract urgency
        if any(word in message.lower() for word in ['urgent', 'high priority', 'critical']):
            task_info['urgency'] = 5
        elif any(word in message.lower() for word in ['low priority', 'not urgent']):
            task_info['urgency'] = 1
        
        # Extract deadline
        if 'today' in message.lower():
            task_info['deadline'] = datetime.now().date()
        elif 'tomorrow' in message.lower():
            task_info['deadline'] = (datetime.now() + timedelta(days=1)).date()
        elif 'next week' in message.lower():
            task_info['deadline'] = (datetime.now() + timedelta(days=7)).date()
        
        return task_info
    
    def process_message(self, message):
        """Main processing logic"""
        intent = self.analyze_intent(message)
        tasks = self.get_tasks_data()
        
        if intent == 'create_task':
            task_info = self.extract_task_info(message)
            if task_info['title']:
                return {
                    'response': f"I can help you create a task: '{task_info['title']}'. Would you like me to add it?",
                    'action': 'create_task',
                    'data': task_info
                }
            else:
                return {
                    'response': "I'd love to help you create a task! Please tell me the task title. For example: 'Add task: Submit report'",
                    'action': None
                }
        
        elif intent == 'count_tasks':
            total = len(tasks)
            pending = len([t for t in tasks if t['status'] == 'Pending'])
            completed = len([t for t in tasks if t['status'] == 'Completed'])
            return {
                'response': f"You have {total} total tasks: {pending} pending and {completed} completed. Keep up the great work! 💪",
                'action': None
            }
        
        elif intent == 'overdue_tasks':
            today = datetime.now().date()
            overdue = [t for t in tasks if t['deadline'] and datetime.strptime(str(t['deadline']), '%Y-%m-%d').date() < today and t['status'] != 'Completed']
            if overdue:
                task_list = '\n'.join([f"• {t['title']} (due {t['deadline']})" for t in overdue[:5]])
                return {
                    'response': f"You have {len(overdue)} overdue task(s):\n{task_list}\n\nLet's tackle these first! 🎯",
                    'action': None
                }
            else:
                return {
                    'response': "Great news! You have no overdue tasks. You're on track! ✅",
                    'action': None
                }
        
        elif intent == 'today_tasks':
            today = datetime.now().date()
            today_tasks = [t for t in tasks if t['deadline'] and datetime.strptime(str(t['deadline']), '%Y-%m-%d').date() == today]
            if today_tasks:
                task_list = '\n'.join([f"• {t['title']} ({t['priority_level']} priority)" for t in today_tasks])
                return {
                    'response': f"You have {len(today_tasks)} task(s) due today:\n{task_list}\n\nYou've got this! 💪",
                    'action': None
                }
            else:
                return {
                    'response': "No tasks due today! You're ahead of schedule. 🎉",
                    'action': None
                }
        
        elif intent == 'high_priority':
            high_priority = [t for t in tasks if t['priority_level'] == 'High' and t['status'] != 'Completed']
            if high_priority:
                task_list = '\n'.join([f"• {t['title']} (due {t['deadline']})" for t in high_priority[:5]])
                return {
                    'response': f"You have {len(high_priority)} high priority task(s):\n{task_list}\n\nThese need your attention! 🔥",
                    'action': None
                }
            else:
                return {
                    'response': "No high priority tasks at the moment. Great job staying on top of things! ⭐",
                    'action': None
                }
        
        elif intent == 'completed_tasks':
            completed = [t for t in tasks if t['status'] == 'Completed']
            return {
                'response': f"You've completed {len(completed)} tasks! That's amazing progress! 🎉\n\nKeep up the excellent work!",
                'action': None
            }
        
        elif intent == 'pending_tasks':
            pending = [t for t in tasks if t['status'] == 'Pending']
            if pending:
                task_list = '\n'.join([f"• {t['title']}" for t in pending[:5]])
                more = f"\n...and {len(pending) - 5} more" if len(pending) > 5 else ""
                return {
                    'response': f"You have {len(pending)} pending task(s):\n{task_list}{more}",
                    'action': None
                }
            else:
                return {
                    'response': "All tasks are in progress or completed! You're doing great! 🌟",
                    'action': None
                }
        
        elif intent == 'recommend_task':
            # Smart recommendation based on priority and deadline
            pending = [t for t in tasks if t['status'] != 'Completed']
            if not pending:
                return {
                    'response': "You have no pending tasks! Time to add new goals or take a well-deserved break! 🎉",
                    'action': None
                }
            
            # Prioritize by: overdue > due today > high priority > earliest deadline
            today = datetime.now().date()
            overdue = [t for t in pending if t['deadline'] and datetime.strptime(str(t['deadline']), '%Y-%m-%d').date() < today]
            
            if overdue:
                task = overdue[0]
                return {
                    'response': f"I recommend working on '{task['title']}' - it's overdue since {task['deadline']}. Let's get it done! 💪",
                    'action': None
                }
            
            high_priority = [t for t in pending if t['priority_level'] == 'High']
            if high_priority:
                task = high_priority[0]
                return {
                    'response': f"I suggest focusing on '{task['title']}' - it's high priority and due {task['deadline']}. 🎯",
                    'action': None
                }
            
            task = pending[0]
            return {
                'response': f"How about working on '{task['title']}'? It's next on your list! 📝",
                'action': None
            }
        
        elif intent == 'analytics':
            total = len(tasks)
            completed = len([t for t in tasks if t['status'] == 'Completed'])
            completion_rate = (completed / total * 100) if total > 0 else 0
            avg_urgency = sum([t['urgency'] for t in tasks]) / total if total > 0 else 0
            
            return {
                'response': f"📊 Your Productivity Stats:\n\n• Total Tasks: {total}\n• Completed: {completed}\n• Completion Rate: {completion_rate:.1f}%\n• Avg Urgency: {avg_urgency:.1f}/5\n\nYou're making great progress! 🚀",
                'action': None
            }
        
        elif intent == 'help':
            return {
                'response': """🤖 I'm your AI Task Assistant! Here's what I can do:

📝 Task Management:
• "Add task: [title]" - Create new task
• "How many tasks?" - Get task count
• "What's overdue?" - Show overdue tasks
• "Tasks due today?" - Today's tasks

🎯 Recommendations:
• "What should I work on?" - Get smart suggestions
• "Show high priority tasks" - Filter by priority

📊 Analytics:
• "Show my productivity" - View stats
• "How many completed?" - Completion count

Just ask me anything about your tasks! 💬""",
                'action': None
            }
        
        else:
            # General response with context
            if tasks:
                pending = len([t for t in tasks if t['status'] != 'Completed'])
                return {
                    'response': f"I'm here to help! You currently have {pending} pending task(s). Ask me about your tasks, or say 'help' to see what I can do! 😊",
                    'action': None
                }
            else:
                return {
                    'response': "Hello! I'm your AI task assistant. You don't have any tasks yet. Would you like to create one? Just say 'Add task: [your task]' 📝",
                    'action': None
                }

@chatbot_bp.route("/chat", methods=["POST"])
def chat():
    try:
        if not require_login():
            return jsonify({"response": "Please login to use the assistant"}), 401
        
        data = request.json
        message = data.get("message", "").strip()
        
        if not message:
            return jsonify({"response": "Please send a message"}), 400
        
        user_id = session.get("user_id")
        assistant = TaskAssistant(user_id)
        result = assistant.process_message(message)
        
        return jsonify(result), 200
    
    except Exception as e:
        print(f"Chatbot error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"response": "Sorry, I encountered an error. Please try again."}), 500
