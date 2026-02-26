from flask import Blueprint, request, session, jsonify
from db_connection import get_db_connection
from datetime import datetime

history_bp = Blueprint('history_bp', __name__)

def log_task_history(task_id, user_id, action_type, field_changed=None, old_value=None, new_value=None):
    """Helper function to log task history"""
    try:
        conn = get_db_connection()
        if not conn:
            return False
        
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO task_history 
               (task_id, user_id, action_type, field_changed, old_value, new_value) 
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (task_id, user_id, action_type, field_changed, str(old_value) if old_value else None, str(new_value) if new_value else None)
        )
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Error logging history: {e}")
        return False

@history_bp.route("/task/<int:task_id>", methods=["GET"])
def get_task_history(task_id):
    """Get complete history for a specific task"""
    try:
        if "user_id" not in session:
            return jsonify({"success": False, "message": "Not logged in"}), 401
        
        conn = get_db_connection()
        if not conn:
            return jsonify({"success": False, "message": "Database error"}), 500
        
        cursor = conn.cursor(dictionary=True)
        
        # Verify task belongs to user
        cursor.execute("SELECT user_id FROM tasks WHERE task_id=%s", (task_id,))
        task = cursor.fetchone()
        
        if not task or task['user_id'] != session['user_id']:
            cursor.close()
            conn.close()
            return jsonify({"success": False, "message": "Task not found"}), 404
        
        # Get history
        cursor.execute(
            """SELECT h.*, u.name as user_name 
               FROM task_history h
               JOIN users u ON h.user_id = u.user_id
               WHERE h.task_id = %s
               ORDER BY h.changed_at DESC""",
            (task_id,)
        )
        history = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return jsonify({"success": True, "history": history})
    
    except Exception as e:
        print(f"Error getting history: {e}")
        return jsonify({"success": False, "message": "Server error"}), 500

@history_bp.route("/recent", methods=["GET"])
def get_recent_history():
    """Get recent activity for current user"""
    try:
        if "user_id" not in session:
            return jsonify({"success": False, "message": "Not logged in"}), 401
        
        limit = request.args.get('limit', 20, type=int)
        
        conn = get_db_connection()
        if not conn:
            return jsonify({"success": False, "message": "Database error"}), 500
        
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute(
            """SELECT h.*, t.title as task_title, u.name as user_name
               FROM task_history h
               JOIN tasks t ON h.task_id = t.task_id
               JOIN users u ON h.user_id = u.user_id
               WHERE t.user_id = %s
               ORDER BY h.changed_at DESC
               LIMIT %s""",
            (session['user_id'], limit)
        )
        history = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return jsonify({"success": True, "history": history})
    
    except Exception as e:
        print(f"Error getting recent history: {e}")
        return jsonify({"success": False, "message": "Server error"}), 500

@history_bp.route("/stats", methods=["GET"])
def get_history_stats():
    """Get activity statistics"""
    try:
        if "user_id" not in session:
            return jsonify({"success": False, "message": "Not logged in"}), 401
        
        conn = get_db_connection()
        if not conn:
            return jsonify({"success": False, "message": "Database error"}), 500
        
        cursor = conn.cursor(dictionary=True)
        
        # Total actions
        cursor.execute(
            """SELECT COUNT(*) as total_actions
               FROM task_history h
               JOIN tasks t ON h.task_id = t.task_id
               WHERE t.user_id = %s""",
            (session['user_id'],)
        )
        total = cursor.fetchone()
        
        # Actions by type
        cursor.execute(
            """SELECT action_type, COUNT(*) as count
               FROM task_history h
               JOIN tasks t ON h.task_id = t.task_id
               WHERE t.user_id = %s
               GROUP BY action_type
               ORDER BY count DESC""",
            (session['user_id'],)
        )
        by_type = cursor.fetchall()
        
        # Recent activity (last 7 days)
        cursor.execute(
            """SELECT DATE(changed_at) as date, COUNT(*) as count
               FROM task_history h
               JOIN tasks t ON h.task_id = t.task_id
               WHERE t.user_id = %s
               AND changed_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
               GROUP BY DATE(changed_at)
               ORDER BY date DESC""",
            (session['user_id'],)
        )
        recent = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            "success": True,
            "stats": {
                "total_actions": total['total_actions'],
                "by_type": by_type,
                "last_7_days": recent
            }
        })
    
    except Exception as e:
        print(f"Error getting stats: {e}")
        return jsonify({"success": False, "message": "Server error"}), 500
