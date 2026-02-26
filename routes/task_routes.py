from flask import Blueprint, request, jsonify, session, send_file
from db_connection import get_db_connection
import traceback
import csv
import io
import re
from datetime import datetime, date

task_bp = Blueprint("task_bp", __name__)

def require_login():
    return 'user_id' in session

def ensure_notifications_table(cursor):
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS notifications (
            notification_id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            title VARCHAR(200) NOT NULL,
            message TEXT NOT NULL,
            type VARCHAR(50) DEFAULT 'info',
            is_read BOOLEAN DEFAULT FALSE,
            task_id INT NULL,
            for_date DATE NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE KEY uniq_task_notif (user_id, type, task_id, for_date)
        )
        """
    )

def _ics_escape(value):
    text = str(value or "")
    text = text.replace("\\", "\\\\").replace(",", "\\,").replace(";", "\\;")
    return text.replace("\n", "\\n")

def _ics_unescape(value):
    text = str(value or "")
    text = text.replace("\\n", "\n")
    text = text.replace("\\,", ",").replace("\\;", ";").replace("\\\\", "\\")
    return text

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

@task_bp.route("/add", methods=["POST"])
def add_task():
    try:
        if not require_login():
            return jsonify({"message":"Unauthorized - please login"}), 401

        data = request.get_json()
        if not data:
            return jsonify({"message":"Invalid request data"}), 400

        title = data.get("title", "").strip()
        if not title:
            return jsonify({"message":"Title is required"}), 400
        
        description = data.get("description", "").strip()
        deadline = data.get("deadline")
        
        try:
            urgency = int(data.get("urgency", 1))
            complexity = int(data.get("complexity", 1))
            est_hours = float(data.get("est_hours", 1.0))
        except (ValueError, TypeError):
            return jsonify({"message":"Invalid numeric values"}), 400
        
        priority_level = data.get("priority_level")
        status = data.get("status", "Pending")
        user_id = session.get("user_id")

        conn = get_db_connection()
        if not conn:
            return jsonify({"message":"DB connection failed"}), 500

        cursor = conn.cursor()
        query = """
        INSERT INTO tasks (user_id, title, description, deadline, urgency, complexity, est_hours, priority_level, status)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """
        cursor.execute(query, (user_id, title, description, deadline, urgency, complexity, est_hours, priority_level, status))
        conn.commit()
        task_id = cursor.lastrowid
        
        # Log task creation
        log_task_history(task_id, user_id, 'CREATED', 'task', None, title)
        
        # Award points for task creation
        try:
            cursor.execute("UPDATE users SET points = points + 10 WHERE user_id=%s", (user_id,))
            conn.commit()
        except Exception as e:
            print(f"Points update failed (column may not exist): {e}")

        cursor.close()
        conn.close()

        return jsonify({"message": "Task added", "task_id": task_id}), 201

    except Exception as e:
        print(f"Exception in add_task: {e}")
        traceback.print_exc()
        return jsonify({"message":"Server error"}), 500

@task_bp.route("/all", methods=["GET"])
def get_all_tasks():
    try:
        if not require_login():
            return jsonify({"message":"Unauthorized - please login"}), 401

        user_id = session.get("user_id")
        conn = get_db_connection()
        if not conn:
            return jsonify({"message":"DB connection failed"}), 500
        
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM tasks WHERE user_id=%s ORDER BY created_at DESC", (user_id,))
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return jsonify(rows), 200

    except Exception as e:
        print(f"Exception in get_all_tasks: {e}")
        traceback.print_exc()
        return jsonify({"message":"Server error"}), 500

@task_bp.route("/search", methods=["GET"])
def search_tasks():
    try:
        if not require_login():
            return jsonify({"message":"Unauthorized"}), 401

        user_id = session.get("user_id")
        query = request.args.get("q", "").strip()
        status = request.args.get("status", "")
        priority = request.args.get("priority", "")
        
        conn = get_db_connection()
        if not conn:
            return jsonify({"message":"DB connection failed"}), 500

        cursor = conn.cursor(dictionary=True)
        
        sql = "SELECT * FROM tasks WHERE user_id=%s"
        params = [user_id]
        
        if query:
            sql += " AND (title LIKE %s OR description LIKE %s)"
            params.extend([f"%{query}%", f"%{query}%"])
        
        if status:
            sql += " AND status=%s"
            params.append(status)
        
        if priority:
            sql += " AND priority_level=%s"
            params.append(priority)
        
        sql += " ORDER BY created_at DESC"
        
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return jsonify(rows), 200

    except Exception as e:
        print(f"Exception in search_tasks: {e}")
        traceback.print_exc()
        return jsonify({"message":"Server error"}), 500

@task_bp.route("/export/csv", methods=["GET"])
def export_csv():
    try:
        if not require_login():
            return jsonify({"message":"Unauthorized"}), 401

        user_id = session.get("user_id")
        conn = get_db_connection()
        if not conn:
            return jsonify({"message":"DB connection failed"}), 500

        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM tasks WHERE user_id=%s ORDER BY created_at DESC", (user_id,))
        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        # Create CSV in memory
        output = io.StringIO()
        if rows:
            writer = csv.DictWriter(output, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
        
        # Create response
        output.seek(0)
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8')),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'tasks_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        )

    except Exception as e:
        print(f"Exception in export_csv: {e}")
        traceback.print_exc()
        return jsonify({"message":"Server error"}), 500

@task_bp.route("/update/<int:task_id>", methods=["PUT"])
def update_task(task_id):
    try:
        if not require_login():
            return jsonify({"message":"Unauthorized"}), 401

        data = request.get_json()
        if not data:
            return jsonify({"message":"Invalid request data"}), 400

        user_id = session.get("user_id")
        conn = get_db_connection()
        if not conn:
            return jsonify({"message":"DB connection failed"}), 500

        cursor = conn.cursor()
        
        # Get old values for history
        cursor.execute("SELECT * FROM tasks WHERE task_id=%s AND user_id=%s", (task_id, user_id))
        old_task = cursor.fetchone()
        if not old_task:
            cursor.close()
            conn.close()
            return jsonify({"message":"Task not found or unauthorized"}), 404
        
        updates = []
        values = []
        
        if "title" in data:
            updates.append("title=%s")
            values.append(data["title"])
        if "description" in data:
            updates.append("description=%s")
            values.append(data["description"])
        if "deadline" in data:
            updates.append("deadline=%s")
            values.append(data["deadline"])
            # Log deadline change
            if str(old_task[4]) != str(data["deadline"]):
                log_task_history(task_id, user_id, 'DEADLINE_CHANGED', 'deadline', old_task[4], data["deadline"])
        if "urgency" in data:
            updates.append("urgency=%s")
            values.append(int(data["urgency"]))
        if "complexity" in data:
            updates.append("complexity=%s")
            values.append(int(data["complexity"]))
        if "est_hours" in data:
            updates.append("est_hours=%s")
            values.append(float(data["est_hours"]))
        if "priority_level" in data:
            updates.append("priority_level=%s")
            values.append(data["priority_level"])
            # Log priority change
            if old_task[8] != data["priority_level"]:
                log_task_history(task_id, user_id, 'PRIORITY_CHANGED', 'priority_level', old_task[8], data["priority_level"])
        if "status" in data:
            updates.append("status=%s")
            values.append(data["status"])
            # Log status change
            if old_task[9] != data["status"]:
                log_task_history(task_id, user_id, 'STATUS_CHANGED', 'status', old_task[9], data["status"])
            # Award points for completing task
            if data["status"] == "Completed" and old_task[9] != "Completed":
                try:
                    cursor.execute("UPDATE users SET points = points + 50 WHERE user_id=%s", (user_id,))
                    conn.commit()
                    log_task_history(task_id, user_id, 'COMPLETED', 'status', old_task[9], 'Completed')
                except Exception as e:
                    print(f"Points update failed (column may not exist): {e}")
        
        if not updates:
            cursor.close()
            conn.close()
            return jsonify({"message":"No fields to update"}), 400
        
        values.extend([task_id, user_id])
        query = f"UPDATE tasks SET {', '.join(updates)} WHERE task_id=%s AND user_id=%s"
        
        cursor.execute(query, values)
        conn.commit()
        
        if cursor.rowcount == 0:
            cursor.close()
            conn.close()
            return jsonify({"message":"Task not found or unauthorized"}), 404
        
        # Log general update if no specific field was logged
        if updates and not any(field in data for field in ['status', 'priority_level', 'deadline']):
            log_task_history(task_id, user_id, 'UPDATED', 'multiple_fields', None, None)
        
        cursor.close()
        conn.close()
        
        return jsonify({"message":"Task updated successfully"}), 200

    except Exception as e:
        print(f"Exception in update_task: {e}")
        traceback.print_exc()
        return jsonify({"message":"Server error"}), 500

@task_bp.route("/delete/<int:task_id>", methods=["DELETE"])
def delete_task(task_id):
    try:
        if not require_login():
            return jsonify({"message":"Unauthorized"}), 401

        user_id = session.get("user_id")
        conn = get_db_connection()
        if not conn:
            return jsonify({"message":"DB connection failed"}), 500

        cursor = conn.cursor()
        
        # Get task title for history
        cursor.execute("SELECT title FROM tasks WHERE task_id=%s AND user_id=%s", (task_id, user_id))
        task = cursor.fetchone()
        if task:
            log_task_history(task_id, user_id, 'DELETED', 'task', task[0], None)
        
        cursor.execute("DELETE FROM tasks WHERE task_id=%s AND user_id=%s", (task_id, user_id))
        conn.commit()
        
        if cursor.rowcount == 0:
            cursor.close()
            conn.close()
            return jsonify({"message":"Task not found or unauthorized"}), 404
        
        cursor.close()
        conn.close()
        
        return jsonify({"message":"Task deleted successfully"}), 200

    except Exception as e:
        print(f"Exception in delete_task: {e}")
        traceback.print_exc()
        return jsonify({"message":"Server error"}), 500

@task_bp.route("/analytics", methods=["GET"])
def get_analytics():
    try:
        if not require_login():
            return jsonify({"message":"Unauthorized"}), 401

        user_id = session.get("user_id")
        conn = get_db_connection()
        if not conn:
            return jsonify({"message":"DB connection failed"}), 500

        cursor = conn.cursor(dictionary=True)
        
        # Total tasks
        cursor.execute("SELECT COUNT(*) as total FROM tasks WHERE user_id=%s", (user_id,))
        total = cursor.fetchone()["total"]
        
        # Tasks by status
        cursor.execute("""
            SELECT status, COUNT(*) as count 
            FROM tasks WHERE user_id=%s 
            GROUP BY status
        """, (user_id,))
        by_status = cursor.fetchall()
        
        # Tasks by priority
        cursor.execute("""
            SELECT priority_level, COUNT(*) as count 
            FROM tasks WHERE user_id=%s AND priority_level IS NOT NULL
            GROUP BY priority_level
        """, (user_id,))
        by_priority = cursor.fetchall()
        
        # Deadline risk (tasks due in next 3 days)
        cursor.execute("""
            SELECT COUNT(*) as at_risk 
            FROM tasks 
            WHERE user_id=%s AND status != 'Completed' 
            AND deadline BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 3 DAY)
        """, (user_id,))
        at_risk = cursor.fetchone()["at_risk"]
        
        # Overdue tasks
        cursor.execute("""
            SELECT COUNT(*) as overdue 
            FROM tasks 
            WHERE user_id=%s AND status != 'Completed' 
            AND deadline < CURDATE()
        """, (user_id,))
        overdue = cursor.fetchone()["overdue"]
        
        # Completion rate
        cursor.execute("""
            SELECT 
                COUNT(CASE WHEN status='Completed' THEN 1 END) as completed,
                COUNT(*) as total
            FROM tasks WHERE user_id=%s
        """, (user_id,))
        completion = cursor.fetchone()
        completion_rate = (completion["completed"] / completion["total"] * 100) if completion["total"] > 0 else 0
        
        # Task statistics
        cursor.execute("""
            SELECT 
                AVG(est_hours) as avg_hours,
                AVG(urgency) as avg_urgency,
                AVG(complexity) as avg_complexity
            FROM tasks WHERE user_id=%s
        """, (user_id,))
        stats = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            "total_tasks": total,
            "by_status": by_status,
            "by_priority": by_priority,
            "at_risk": at_risk,
            "overdue": overdue,
            "completion_rate": round(completion_rate, 2),
            "avg_hours": round(float(stats["avg_hours"] or 0), 2),
            "avg_urgency": round(float(stats["avg_urgency"] or 0), 2),
            "avg_complexity": round(float(stats["avg_complexity"] or 0), 2)
        }), 200

    except Exception as e:
        print(f"Exception in get_analytics: {e}")
        traceback.print_exc()
        return jsonify({"message":"Server error"}), 500


@task_bp.route("/calendar/export.ics", methods=["GET"])
def export_ics():
    try:
        if not require_login():
            return jsonify({"message": "Unauthorized"}), 401

        user_id = session.get("user_id")
        conn = get_db_connection()
        if not conn:
            return jsonify({"message": "DB connection failed"}), 500

        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT task_id, title, description, deadline, status, priority_level
            FROM tasks
            WHERE user_id=%s AND deadline IS NOT NULL
            ORDER BY deadline ASC
            """,
            (user_id,),
        )
        tasks = cursor.fetchall()
        cursor.close()
        conn.close()

        lines = [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//PriorityIQ//Task Calendar//EN",
            "CALSCALE:GREGORIAN",
            "METHOD:PUBLISH",
        ]

        now_stamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        for task in tasks:
            if not task.get("deadline"):
                continue
            due_date = task["deadline"]
            if hasattr(due_date, "strftime"):
                due_str = due_date.strftime("%Y%m%d")
            else:
                due_str = str(due_date).replace("-", "")
            uid = f"task-{task['task_id']}-priorityiq"
            description = task.get("description") or ""
            meta = f"Status: {task.get('status') or 'Pending'} | Priority: {task.get('priority_level') or 'NA'}"
            full_description = f"{description}\n{meta}".strip()
            lines.extend(
                [
                    "BEGIN:VEVENT",
                    f"UID:{uid}",
                    f"DTSTAMP:{now_stamp}",
                    f"DTSTART;VALUE=DATE:{due_str}",
                    f"SUMMARY:{_ics_escape(task.get('title') or 'Task')}",
                    f"DESCRIPTION:{_ics_escape(full_description)}",
                    "END:VEVENT",
                ]
            )

        lines.append("END:VCALENDAR")
        payload = "\r\n".join(lines) + "\r\n"
        return send_file(
            io.BytesIO(payload.encode("utf-8")),
            mimetype="text/calendar",
            as_attachment=True,
            download_name=f"priorityiq_tasks_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.ics",
        )
    except Exception as e:
        print(f"Exception in export_ics: {e}")
        traceback.print_exc()
        return jsonify({"message": "Server error"}), 500


@task_bp.route("/calendar/import.ics", methods=["POST"])
def import_ics():
    try:
        if not require_login():
            return jsonify({"message": "Unauthorized"}), 401

        data = request.get_json() or {}
        ics_text = data.get("ics_text")
        default_status = data.get("status", "Pending")
        if not ics_text:
            return jsonify({"message": "ics_text is required"}), 400

        events = []
        current = {}
        for line in ics_text.splitlines():
            raw = line.strip()
            if raw == "BEGIN:VEVENT":
                current = {}
            elif raw == "END:VEVENT":
                if current:
                    events.append(current)
                current = {}
            elif ":" in raw:
                key, value = raw.split(":", 1)
                current[key] = value

        user_id = session.get("user_id")
        conn = get_db_connection()
        if not conn:
            return jsonify({"message": "DB connection failed"}), 500
        cursor = conn.cursor()

        created = 0
        for event in events:
            title = _ics_unescape(event.get("SUMMARY", "")).strip() or "Imported Task"
            description = _ics_unescape(event.get("DESCRIPTION", "")).strip()

            dt_value = event.get("DTSTART;VALUE=DATE") or event.get("DTSTART")
            deadline = None
            if dt_value:
                match = re.match(r"^(\d{4})(\d{2})(\d{2})", dt_value)
                if match:
                    deadline = f"{match.group(1)}-{match.group(2)}-{match.group(3)}"

            cursor.execute(
                """
                INSERT INTO tasks (user_id, title, description, deadline, urgency, complexity, est_hours, priority_level, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (user_id, title, description, deadline, 2, 2, 1.0, None, default_status),
            )
            created += 1

        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"message": "ICS imported successfully", "created": created}), 201
    except Exception as e:
        print(f"Exception in import_ics: {e}")
        traceback.print_exc()
        return jsonify({"message": "Server error"}), 500


@task_bp.route("/notifications", methods=["GET"])
def get_notifications():
    try:
        if not require_login():
            return jsonify({"message": "Unauthorized"}), 401

        user_id = session.get("user_id")
        limit = request.args.get("limit", 50, type=int)
        limit = max(1, min(limit, 200))

        conn = get_db_connection()
        if not conn:
            return jsonify({"message": "DB connection failed"}), 500
        cursor = conn.cursor(dictionary=True)

        ensure_notifications_table(cursor)
        today = date.today()

        cursor.execute(
            """
            SELECT task_id, title, deadline
            FROM tasks
            WHERE user_id=%s AND status != 'Completed' AND deadline IS NOT NULL
            """,
            (user_id,),
        )
        tasks = cursor.fetchall()

        for task in tasks:
            deadline = task.get("deadline")
            if not deadline:
                continue
            days_left = (deadline - today).days
            notif_type = None
            title = None
            message = None
            if days_left < 0:
                notif_type = "overdue"
                title = "Task Overdue"
                message = f"'{task['title']}' is overdue."
            elif days_left == 0:
                notif_type = "due_today"
                title = "Due Today"
                message = f"'{task['title']}' is due today."
            elif days_left == 1:
                notif_type = "due_tomorrow"
                title = "Due Tomorrow"
                message = f"'{task['title']}' is due tomorrow."

            if notif_type:
                cursor.execute(
                    """
                    INSERT INTO notifications (user_id, title, message, type, task_id, for_date)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE title=VALUES(title), message=VALUES(message)
                    """,
                    (user_id, title, message, notif_type, task["task_id"], today),
                )

        conn.commit()

        cursor.execute(
            """
            SELECT notification_id, title, message, type, is_read, task_id, for_date, created_at
            FROM notifications
            WHERE user_id=%s
            ORDER BY created_at DESC
            LIMIT %s
            """,
            (user_id, limit),
        )
        rows = cursor.fetchall()
        for row in rows:
            row["created_at"] = str(row["created_at"]) if row.get("created_at") else None
            row["for_date"] = str(row["for_date"]) if row.get("for_date") else None

        cursor.close()
        conn.close()
        return jsonify({"notifications": rows}), 200
    except Exception as e:
        print(f"Exception in get_notifications: {e}")
        traceback.print_exc()
        return jsonify({"message": "Server error"}), 500


@task_bp.route("/notifications/mark-read", methods=["POST"])
def mark_notifications_read():
    try:
        if not require_login():
            return jsonify({"message": "Unauthorized"}), 401

        user_id = session.get("user_id")
        data = request.get_json() or {}
        mark_all = bool(data.get("all", False))
        ids = data.get("ids") or []

        conn = get_db_connection()
        if not conn:
            return jsonify({"message": "DB connection failed"}), 500
        cursor = conn.cursor()
        ensure_notifications_table(cursor)

        if mark_all:
            cursor.execute("UPDATE notifications SET is_read=TRUE WHERE user_id=%s", (user_id,))
        else:
            safe_ids = [int(i) for i in ids if str(i).isdigit()]
            if not safe_ids:
                cursor.close()
                conn.close()
                return jsonify({"message": "ids must be a non-empty list when all=false"}), 400
            placeholders = ", ".join(["%s"] * len(safe_ids))
            cursor.execute(
                f"UPDATE notifications SET is_read=TRUE WHERE user_id=%s AND notification_id IN ({placeholders})",
                [user_id] + safe_ids,
            )

        conn.commit()
        affected = cursor.rowcount
        cursor.close()
        conn.close()
        return jsonify({"message": "Notifications updated", "affected": affected}), 200
    except Exception as e:
        print(f"Exception in mark_notifications_read: {e}")
        traceback.print_exc()
        return jsonify({"message": "Server error"}), 500
