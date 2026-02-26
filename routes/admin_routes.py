from flask import Blueprint, request, session, jsonify, send_file
from db_connection import get_db_connection
import io
import json
from datetime import datetime

admin_bp = Blueprint('admin_bp', __name__)

ROLE_PERMISSIONS = {
    "super_admin": {
        "view_console",
        "manage_users",
        "manage_tasks",
        "manage_admins",
        "manage_notifications",
        "view_audit",
        "manage_backup",
    },
    "manager": {
        "view_console",
        "manage_users",
        "manage_tasks",
        "manage_notifications",
        "view_audit",
    },
    "support": {
        "view_console",
        "manage_tasks",
        "manage_notifications",
        "view_audit",
    },
    "viewer": {
        "view_console",
        "view_audit",
    },
}


def table_exists(cursor, table_name):
    cursor.execute("SHOW TABLES LIKE %s", (table_name,))
    return cursor.fetchone() is not None

def column_exists(cursor, table_name, column_name):
    cursor.execute(
        """
        SELECT 1
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = %s
          AND COLUMN_NAME = %s
        LIMIT 1
        """,
        (table_name, column_name),
    )
    return cursor.fetchone() is not None

def ensure_admin_role_overrides_table(cursor):
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS admin_role_overrides (
            email VARCHAR(255) PRIMARY KEY,
            role VARCHAR(32) NOT NULL DEFAULT 'super_admin',
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )
        """
    )

def ensure_admin_audit_logs_table(cursor):
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS admin_audit_logs (
            log_id INT AUTO_INCREMENT PRIMARY KEY,
            admin_user_id INT NULL,
            admin_email VARCHAR(255) NOT NULL,
            admin_role VARCHAR(32) NOT NULL,
            action VARCHAR(100) NOT NULL,
            entity_type VARCHAR(64) NULL,
            entity_id VARCHAR(64) NULL,
            details TEXT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

def get_admin_role(cursor, email, user_id):
    role = None
    ensure_admin_role_overrides_table(cursor)
    cursor.execute("SELECT role FROM admin_role_overrides WHERE email=%s", (email,))
    override = cursor.fetchone()
    if override and override.get("role"):
        role = override["role"]

    if not role and table_exists(cursor, "admin_credentials"):
        cursor.execute(
            """
            SELECT COLUMN_NAME
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME='admin_credentials' AND COLUMN_NAME='role'
            """
        )
        if cursor.fetchone():
            cursor.execute("SELECT role FROM admin_credentials WHERE email=%s AND active=TRUE", (email,))
            row = cursor.fetchone()
            if row and row.get("role"):
                role = row["role"]

    if not role:
        cursor.execute(
            """
            SELECT COLUMN_NAME
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME='users' AND COLUMN_NAME='admin_role'
            """
        )
        if cursor.fetchone():
            cursor.execute("SELECT admin_role FROM users WHERE user_id=%s", (user_id,))
            row = cursor.fetchone()
            if row and row.get("admin_role"):
                role = row["admin_role"]

    return role if role in ROLE_PERMISSIONS else "super_admin"

def get_admin_context():
    if "user_id" not in session or "email" not in session:
        return {"is_admin": False, "role": None, "permissions": []}

    conn = get_db_connection()
    if not conn:
        return {"is_admin": False, "role": None, "permissions": []}

    cursor = conn.cursor(dictionary=True)
    try:
        allowed = False
        if table_exists(cursor, "admin_credentials"):
            cursor.execute(
                "SELECT 1 FROM admin_credentials WHERE email=%s AND active=TRUE",
                (session["email"],)
            )
            allowed = cursor.fetchone() is not None
        else:
            cursor.execute("SELECT is_admin FROM users WHERE user_id=%s", (session["user_id"],))
            user = cursor.fetchone()
            allowed = bool(user and user.get("is_admin", False))

        if not allowed:
            return {"is_admin": False, "role": None, "permissions": []}

        role = get_admin_role(cursor, session["email"], session["user_id"])
        return {
            "is_admin": True,
            "role": role,
            "permissions": sorted(list(ROLE_PERMISSIONS.get(role, set()))),
        }
    finally:
        cursor.close()
        conn.close()

def is_admin():
    return get_admin_context()["is_admin"]

def require_admin_permission(permission):
    context = get_admin_context()
    if not context["is_admin"]:
        return None, jsonify({"success": False, "message": "Admin access required"}), 403
    if permission and permission not in ROLE_PERMISSIONS.get(context["role"], set()):
        return None, jsonify({"success": False, "message": f"Permission denied: {permission}"}), 403
    return context, None, None

def log_admin_action(action, entity_type=None, entity_id=None, details=None):
    context = get_admin_context()
    if not context["is_admin"]:
        return

    conn = get_db_connection()
    if not conn:
        return

    cursor = conn.cursor()
    try:
        ensure_admin_audit_logs_table(cursor)
        cursor.execute(
            """
            INSERT INTO admin_audit_logs
            (admin_user_id, admin_email, admin_role, action, entity_type, entity_id, details)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                session.get("user_id"),
                session.get("email"),
                context["role"],
                action,
                entity_type,
                str(entity_id) if entity_id is not None else None,
                json.dumps(details) if details is not None else None,
            ),
        )
        conn.commit()
    except Exception:
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

# Departments
@admin_bp.route("/departments")
def get_departments():
    if not is_admin():
        return jsonify({"success": False, "message": "Admin access required"}), 403
    conn = get_db_connection()
    if not conn:
        return jsonify({"success": False, "message": "Database connection failed"}), 500
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM departments ORDER BY dept_name")
    depts = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(depts)

# Exam Schedules
@admin_bp.route("/exams/add", methods=["POST"])
def add_exam():
    if not is_admin():
        return jsonify({"success": False, "message": "Admin access required"}), 403
    
    try:
        data = request.get_json() or {}
        required = ["dept_id", "exam_date", "exam_time"]
        missing = [field for field in required if not data.get(field)]
        if missing:
            return jsonify({"success": False, "message": f"Missing required fields: {', '.join(missing)}"}), 400
        
        conn = get_db_connection()
        if not conn:
            return jsonify({"success": False, "message": "Database connection failed"}), 500
        cursor = conn.cursor()
        exam_name = data.get("exam_name") or data.get("subject_name")
        subject = data.get("subject") or data.get("subject_name")
        duration_minutes = data.get("duration_minutes") or data.get("duration_mins")
        room_number = data.get("room_number") or data.get("room_no")
        if not exam_name or not subject or not duration_minutes:
            cursor.close()
            conn.close()
            return jsonify({"success": False, "message": "Exam name, subject, and duration are required"}), 400
        cursor.execute(
            "INSERT INTO exam_schedules (dept_id, exam_name, subject, exam_date, exam_time, duration_minutes, room_number, created_by) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
            (data["dept_id"], exam_name, subject, data["exam_date"], data["exam_time"], duration_minutes, room_number, session["user_id"])
        )
        conn.commit()
        exam_id = cursor.lastrowid
        cursor.close()
        conn.close()
        return jsonify({"success": True, "exam_id": exam_id})
    except Exception as e:
        return jsonify({"success": False, "message": f"Failed to add exam: {str(e)}"}), 500

@admin_bp.route("/exams/all")
def get_exams():
    if not is_admin():
        return jsonify({"success": False, "message": "Admin access required"}), 403
    dept_id = request.args.get("dept_id")
    conn = get_db_connection()
    if not conn:
        return jsonify({"success": False, "message": "Database connection failed"}), 500
    cursor = conn.cursor(dictionary=True)
    if dept_id:
        cursor.execute("""
            SELECT e.*, d.dept_name, d.dept_code 
            FROM exam_schedules e 
            JOIN departments d ON e.dept_id = d.dept_id 
            WHERE e.dept_id=%s 
            ORDER BY e.exam_date, e.exam_time
        """, (dept_id,))
    else:
        cursor.execute("""
            SELECT e.*, d.dept_name, d.dept_code 
            FROM exam_schedules e 
            JOIN departments d ON e.dept_id = d.dept_id 
            ORDER BY e.exam_date, e.exam_time
        """)
    exams = cursor.fetchall()
    cursor.close()
    conn.close()
    
    # Format dates and times for JSON
    for exam in exams:
        if exam.get('exam_date'):
            exam['exam_date'] = str(exam['exam_date'])
        if exam.get('exam_time'):
            exam['exam_time'] = str(exam['exam_time'])
        if exam.get('created_at'):
            exam['created_at'] = str(exam['created_at'])
    
    return jsonify(exams)

@admin_bp.route("/exams/delete/<int:exam_id>", methods=["DELETE"])
def delete_exam(exam_id):
    if not is_admin():
        return jsonify({"success": False, "message": "Admin access required"}), 403
    
    conn = get_db_connection()
    if not conn:
        return jsonify({"success": False, "message": "Database connection failed"}), 500
    cursor = conn.cursor()
    cursor.execute("DELETE FROM exam_schedules WHERE exam_id=%s", (exam_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"success": True})

# College Events
@admin_bp.route("/events/add", methods=["POST"])
def add_event():
    if not is_admin():
        return jsonify({"success": False, "message": "Admin access required"}), 403
    
    data = request.json
    conn = get_db_connection()
    if not conn:
        return jsonify({"success": False, "message": "Database connection failed"}), 500
    cursor = conn.cursor()
    event_time = data.get("event_time") or "00:00:00"
    cursor.execute(
        "INSERT INTO college_events (event_name, event_description, event_date, event_time, venue, event_type, created_by) VALUES (%s, %s, %s, %s, %s, %s, %s)",
        (
            data["event_name"],
            data.get("event_description") or data.get("description"),
            data["event_date"],
            event_time,
            data.get("venue") or data.get("location"),
            data.get("event_type"),
            session["user_id"]
        )
    )
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"success": True})

@admin_bp.route("/events/all")
def get_events():
    if not is_admin():
        return jsonify({"success": False, "message": "Admin access required"}), 403
    conn = get_db_connection()
    if not conn:
        return jsonify({"success": False, "message": "Database connection failed"}), 500
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM college_events ORDER BY event_date DESC")
    events = cursor.fetchall()
    cursor.close()
    conn.close()
    
    # Format dates and times for JSON
    for event in events:
        if event.get('event_date'):
            event['event_date'] = str(event['event_date'])
        if event.get('event_time'):
            event['event_time'] = str(event['event_time'])
        if event.get('created_at'):
            event['created_at'] = str(event['created_at'])
    
    return jsonify(events)

@admin_bp.route("/events/delete/<int:event_id>", methods=["DELETE"])
def delete_event(event_id):
    if not is_admin():
        return jsonify({"success": False, "message": "Admin access required"}), 403
    
    conn = get_db_connection()
    if not conn:
        return jsonify({"success": False, "message": "Database connection failed"}), 500
    cursor = conn.cursor()
    cursor.execute("DELETE FROM college_events WHERE event_id=%s", (event_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"success": True})

# Attendance
@admin_bp.route("/attendance/mark", methods=["POST"])
def mark_attendance():
    if not is_admin():
        return jsonify({"success": False, "message": "Admin access required"}), 403
    
    data = request.json
    email = data.get("email")
    
    conn = get_db_connection()
    if not conn:
        return jsonify({"success": False, "message": "Database connection failed"}), 500
    cursor = conn.cursor(dictionary=True)
    
    # Get user_id from email
    cursor.execute("SELECT user_id FROM users WHERE email=%s", (email,))
    user = cursor.fetchone()
    
    if not user:
        cursor.close()
        conn.close()
        return jsonify({"success": False, "message": "User not found"}), 404
    
    cursor.execute(
        "INSERT INTO attendance (user_id, dept_id, attendance_date, status, marked_by) VALUES (%s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE status=%s, marked_by=%s",
        (user["user_id"], data["dept_id"], data["attendance_date"], data["status"], session["user_id"], data["status"], session["user_id"])
    )
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"success": True})

@admin_bp.route("/attendance/all")
def get_attendance():
    if not is_admin():
        return jsonify({"success": False, "message": "Admin access required"}), 403
    user_id = request.args.get("user_id")
    conn = get_db_connection()
    if not conn:
        return jsonify({"success": False, "message": "Database connection failed"}), 500
    cursor = conn.cursor(dictionary=True)
    if user_id:
        cursor.execute("""
            SELECT a.*, u.name, u.email, d.dept_name 
            FROM attendance a 
            JOIN users u ON a.user_id = u.user_id 
            JOIN departments d ON a.dept_id = d.dept_id 
            WHERE a.user_id=%s 
            ORDER BY a.attendance_date DESC
        """, (user_id,))
    else:
        cursor.execute("""
            SELECT a.*, u.name, u.email, d.dept_name 
            FROM attendance a 
            JOIN users u ON a.user_id = u.user_id 
            JOIN departments d ON a.dept_id = d.dept_id 
            ORDER BY a.attendance_date DESC 
            LIMIT 100
        """)
    records = cursor.fetchall()
    cursor.close()
    conn.close()
    
    # Format dates for JSON
    for record in records:
        if record.get('attendance_date'):
            record['attendance_date'] = str(record['attendance_date'])
        if record.get('created_at'):
            record['created_at'] = str(record['created_at'])
    
    return jsonify(records)

# Announcements
@admin_bp.route("/announcements/add", methods=["POST"])
def add_announcement():
    if not is_admin():
        return jsonify({"success": False, "message": "Admin access required"}), 403
    
    data = request.json
    conn = get_db_connection()
    if not conn:
        return jsonify({"success": False, "message": "Database connection failed"}), 500
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO announcements (title, content, priority, target_audience, dept_id, created_by, expires_at) VALUES (%s, %s, %s, %s, %s, %s, %s)",
        (
            data["title"],
            data["content"],
            data.get("priority", "Medium"),
            data.get("target_audience", "All"),
            data.get("dept_id"),
            session["user_id"],
            data.get("expires_at")
        )
    )
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"success": True})

@admin_bp.route("/announcements/all")
def get_announcements():
    if not is_admin():
        return jsonify({"success": False, "message": "Admin access required"}), 403
    conn = get_db_connection()
    if not conn:
        return jsonify({"success": False, "message": "Database connection failed"}), 500
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM announcements ORDER BY created_at DESC LIMIT 50")
    announcements = cursor.fetchall()
    cursor.close()
    conn.close()
    
    # Format dates for JSON
    for announcement in announcements:
        if announcement.get('created_at'):
            announcement['created_at'] = str(announcement['created_at'])
    
    return jsonify(announcements)

@admin_bp.route("/announcements/delete/<int:announcement_id>", methods=["DELETE"])
def delete_announcement(announcement_id):
    if not is_admin():
        return jsonify({"success": False, "message": "Admin access required"}), 403
    
    conn = get_db_connection()
    if not conn:
        return jsonify({"success": False, "message": "Database connection failed"}), 500
    cursor = conn.cursor()
    cursor.execute("DELETE FROM announcements WHERE announcement_id=%s", (announcement_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"success": True})

@admin_bp.route("/check")
def check_admin():
    context = get_admin_context()
    return jsonify({
        "is_admin": context["is_admin"],
        "role": context["role"],
        "permissions": context["permissions"],
    })


# -------------------------
# Global Admin Console APIs
# -------------------------

@admin_bp.route("/console/overview", methods=["GET"])
def console_overview():
    _, err, status = require_admin_permission("view_console")
    if err:
        return err, status

    conn = get_db_connection()
    if not conn:
        return jsonify({"success": False, "message": "Database connection failed"}), 500

    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT COUNT(*) AS total_users FROM users")
        total_users = cursor.fetchone()["total_users"]

        cursor.execute("SELECT COUNT(*) AS total_tasks FROM tasks")
        total_tasks = cursor.fetchone()["total_tasks"]

        cursor.execute("SELECT COUNT(*) AS completed_tasks FROM tasks WHERE status='Completed'")
        completed_tasks = cursor.fetchone()["completed_tasks"]

        cursor.execute("SELECT COUNT(*) AS admin_users FROM users WHERE is_admin=TRUE")
        admin_users = cursor.fetchone()["admin_users"]

        return jsonify({
            "success": True,
            "overview": {
                "total_users": total_users,
                "total_tasks": total_tasks,
                "completed_tasks": completed_tasks,
                "admin_users": admin_users
            }
        })
    finally:
        cursor.close()
        conn.close()


@admin_bp.route("/console/users", methods=["GET"])
def console_users():
    _, err, status = require_admin_permission("view_console")
    if err:
        return err, status

    conn = get_db_connection()
    if not conn:
        return jsonify({"success": False, "message": "Database connection failed"}), 500

    cursor = conn.cursor(dictionary=True)
    try:
        # Schema-safe query: some installs may not have phone/role/is_admin yet.
        cursor.execute(
            """
            SELECT COLUMN_NAME
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'users'
            """
        )
        user_columns = {row["COLUMN_NAME"] for row in cursor.fetchall()}

        has_phone = "phone" in user_columns
        has_role = "role" in user_columns
        has_is_admin = "is_admin" in user_columns
        has_created_at = "created_at" in user_columns

        phone_select = "u.phone AS phone" if has_phone else "NULL AS phone"
        role_select = "u.role AS role" if has_role else "NULL AS role"
        admin_select = "u.is_admin AS is_admin" if has_is_admin else "FALSE AS is_admin"
        created_at_select = "u.created_at AS created_at" if has_created_at else "NULL AS created_at"

        group_by_parts = ["u.user_id", "u.name", "u.email"]
        if has_phone:
            group_by_parts.append("u.phone")
        if has_role:
            group_by_parts.append("u.role")
        if has_is_admin:
            group_by_parts.append("u.is_admin")
        if has_created_at:
            group_by_parts.append("u.created_at")
        group_by_clause = ", ".join(group_by_parts)
        order_by_clause = "u.created_at DESC, u.user_id DESC" if has_created_at else "u.user_id DESC"

        cursor.execute(
            f"""
            SELECT
                u.user_id,
                u.name,
                u.email,
                {phone_select},
                {role_select},
                {admin_select},
                {created_at_select},
                COUNT(t.task_id) AS task_count,
                SUM(CASE WHEN t.status='Completed' THEN 1 ELSE 0 END) AS completed_count
            FROM users u
            LEFT JOIN tasks t ON u.user_id = t.user_id
            GROUP BY {group_by_clause}
            ORDER BY {order_by_clause}
            """
        )
        users = cursor.fetchall()

        for user in users:
            user["created_at"] = str(user["created_at"]) if user.get("created_at") else None
            user["task_count"] = int(user.get("task_count") or 0)
            user["completed_count"] = int(user.get("completed_count") or 0)
            user["is_admin"] = bool(user.get("is_admin"))

        return jsonify({"success": True, "users": users})
    except Exception as e:
        return jsonify({"success": False, "message": f"Failed to load users: {str(e)}"}), 500
    finally:
        cursor.close()
        conn.close()


@admin_bp.route("/console/users/<int:user_id>", methods=["PUT"])
def console_update_user(user_id):
    _, err, status = require_admin_permission("manage_users")
    if err:
        return err, status

    data = request.get_json() or {}
    allowed_fields = {
        "name": "name",
        "email": "email",
        "phone": "phone",
        "role": "role",
        "is_admin": "is_admin"
    }

    updates = []
    values = []
    for key, column in allowed_fields.items():
        if key in data:
            updates.append(f"{column}=%s")
            values.append(data[key])

    if not updates:
        return jsonify({"success": False, "message": "No fields to update"}), 400

    # Prevent the current admin from accidentally revoking own admin rights.
    if user_id == session.get("user_id") and "is_admin" in data and not bool(data["is_admin"]):
        return jsonify({"success": False, "message": "You cannot remove your own admin access"}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({"success": False, "message": "Database connection failed"}), 500

    cursor = conn.cursor()
    try:
        values.append(user_id)
        cursor.execute(f"UPDATE users SET {', '.join(updates)} WHERE user_id=%s", values)
        conn.commit()
        if cursor.rowcount == 0:
            return jsonify({"success": False, "message": "User not found"}), 404
        log_admin_action("USER_UPDATED", "user", user_id, {"fields": list(data.keys())})
        return jsonify({"success": True, "message": "User updated successfully"})
    finally:
        cursor.close()
        conn.close()


@admin_bp.route("/console/users/<int:user_id>", methods=["DELETE"])
def console_delete_user(user_id):
    _, err, status = require_admin_permission("manage_users")
    if err:
        return err, status

    if user_id == session.get("user_id"):
        return jsonify({"success": False, "message": "You cannot delete your own account"}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({"success": False, "message": "Database connection failed"}), 500

    cursor = conn.cursor()
    try:
        # Delete dependent rows first to avoid FK failures in common schemas.
        if table_exists(cursor, "priority_predictions"):
            cursor.execute("DELETE FROM priority_predictions WHERE task_id IN (SELECT task_id FROM tasks WHERE user_id=%s)", (user_id,))
        if table_exists(cursor, "task_history"):
            if column_exists(cursor, "task_history", "user_id"):
                cursor.execute("DELETE FROM task_history WHERE user_id=%s", (user_id,))
            elif column_exists(cursor, "task_history", "task_id"):
                cursor.execute("DELETE FROM task_history WHERE task_id IN (SELECT task_id FROM tasks WHERE user_id=%s)", (user_id,))
        if table_exists(cursor, "attendance"):
            cursor.execute("DELETE FROM attendance WHERE user_id=%s", (user_id,))
        if table_exists(cursor, "notifications") and column_exists(cursor, "notifications", "user_id"):
            cursor.execute("DELETE FROM notifications WHERE user_id=%s", (user_id,))
        cursor.execute("DELETE FROM tasks WHERE user_id=%s", (user_id,))
        cursor.execute("DELETE FROM users WHERE user_id=%s", (user_id,))

        if cursor.rowcount == 0:
            conn.rollback()
            return jsonify({"success": False, "message": "User not found"}), 404

        conn.commit()
        log_admin_action("USER_DELETED", "user", user_id)
        return jsonify({"success": True, "message": "User deleted successfully"})
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": f"Delete failed: {str(e)}"}), 500
    finally:
        cursor.close()
        conn.close()


@admin_bp.route("/console/tasks", methods=["GET"])
def console_tasks():
    _, err, status = require_admin_permission("view_console")
    if err:
        return err, status

    limit = request.args.get("limit", 200, type=int)
    limit = max(1, min(limit, 500))

    conn = get_db_connection()
    if not conn:
        return jsonify({"success": False, "message": "Database connection failed"}), 500

    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT
                t.task_id,
                t.user_id,
                u.name AS user_name,
                u.email AS user_email,
                t.title,
                t.description,
                t.deadline,
                t.urgency,
                t.complexity,
                t.est_hours,
                t.priority_level,
                t.status,
                t.created_at
            FROM tasks t
            JOIN users u ON t.user_id = u.user_id
            ORDER BY t.created_at DESC
            LIMIT %s
            """,
            (limit,)
        )
        tasks = cursor.fetchall()
        for task in tasks:
            task["deadline"] = str(task["deadline"]) if task.get("deadline") else None
            task["created_at"] = str(task["created_at"]) if task.get("created_at") else None
        return jsonify({"success": True, "tasks": tasks})
    finally:
        cursor.close()
        conn.close()


@admin_bp.route("/console/tasks/<int:task_id>", methods=["PUT"])
def console_update_task(task_id):
    _, err, status = require_admin_permission("manage_tasks")
    if err:
        return err, status

    data = request.get_json() or {}
    allowed_fields = {
        "title": "title",
        "description": "description",
        "deadline": "deadline",
        "urgency": "urgency",
        "complexity": "complexity",
        "est_hours": "est_hours",
        "priority_level": "priority_level",
        "status": "status"
    }

    updates = []
    values = []
    for key, column in allowed_fields.items():
        if key in data:
            updates.append(f"{column}=%s")
            values.append(data[key])

    if not updates:
        return jsonify({"success": False, "message": "No fields to update"}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({"success": False, "message": "Database connection failed"}), 500

    cursor = conn.cursor()
    try:
        values.append(task_id)
        cursor.execute(f"UPDATE tasks SET {', '.join(updates)} WHERE task_id=%s", values)
        conn.commit()
        if cursor.rowcount == 0:
            return jsonify({"success": False, "message": "Task not found"}), 404
        log_admin_action("TASK_UPDATED", "task", task_id, {"fields": list(data.keys())})
        return jsonify({"success": True, "message": "Task updated successfully"})
    finally:
        cursor.close()
        conn.close()


@admin_bp.route("/console/tasks/<int:task_id>", methods=["DELETE"])
def console_delete_task(task_id):
    _, err, status = require_admin_permission("manage_tasks")
    if err:
        return err, status

    conn = get_db_connection()
    if not conn:
        return jsonify({"success": False, "message": "Database connection failed"}), 500

    cursor = conn.cursor()
    try:
        if table_exists(cursor, "priority_predictions"):
            cursor.execute("DELETE FROM priority_predictions WHERE task_id=%s", (task_id,))
        if table_exists(cursor, "task_history"):
            cursor.execute("DELETE FROM task_history WHERE task_id=%s", (task_id,))
        cursor.execute("DELETE FROM tasks WHERE task_id=%s", (task_id,))
        conn.commit()
        if cursor.rowcount == 0:
            return jsonify({"success": False, "message": "Task not found"}), 404
        log_admin_action("TASK_DELETED", "task", task_id)
        return jsonify({"success": True, "message": "Task deleted successfully"})
    finally:
        cursor.close()
        conn.close()


@admin_bp.route("/console/tasks/bulk", methods=["PUT"])
def console_bulk_update_tasks():
    _, err, status = require_admin_permission("manage_tasks")
    if err:
        return err, status

    data = request.get_json() or {}
    task_ids = data.get("task_ids") or []
    action = (data.get("action") or "").strip()
    value = data.get("value")

    if not task_ids or not isinstance(task_ids, list):
        return jsonify({"success": False, "message": "task_ids must be a non-empty array"}), 400

    safe_ids = [int(i) for i in task_ids if str(i).isdigit()]
    if not safe_ids:
        return jsonify({"success": False, "message": "No valid task ids provided"}), 400

    if action not in {"status", "priority", "delete"}:
        return jsonify({"success": False, "message": "action must be one of: status, priority, delete"}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({"success": False, "message": "Database connection failed"}), 500

    cursor = conn.cursor()
    try:
        placeholders = ", ".join(["%s"] * len(safe_ids))
        if action == "delete":
            if table_exists(cursor, "priority_predictions"):
                cursor.execute(f"DELETE FROM priority_predictions WHERE task_id IN ({placeholders})", safe_ids)
            if table_exists(cursor, "task_history"):
                cursor.execute(f"DELETE FROM task_history WHERE task_id IN ({placeholders})", safe_ids)
            cursor.execute(f"DELETE FROM tasks WHERE task_id IN ({placeholders})", safe_ids)
        elif action == "status":
            if not value:
                return jsonify({"success": False, "message": "value is required for status action"}), 400
            cursor.execute(f"UPDATE tasks SET status=%s WHERE task_id IN ({placeholders})", [value] + safe_ids)
        else:
            cursor.execute(f"UPDATE tasks SET priority_level=%s WHERE task_id IN ({placeholders})", [value] + safe_ids)

        affected = cursor.rowcount
        conn.commit()
        log_admin_action("TASKS_BULK_ACTION", "task", None, {"action": action, "task_ids": safe_ids, "value": value, "affected": affected})
        return jsonify({"success": True, "affected": affected})
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": f"Bulk action failed: {str(e)}"}), 500
    finally:
        cursor.close()
        conn.close()


@admin_bp.route("/console/admin-role", methods=["GET"])
def console_admin_role():
    context, err, status = require_admin_permission("view_console")
    if err:
        return err, status
    return jsonify({
        "success": True,
        "role": context["role"],
        "permissions": context["permissions"],
        "available_roles": list(ROLE_PERMISSIONS.keys()),
    })


@admin_bp.route("/console/admin-users", methods=["GET"])
def console_admin_users():
    _, err, status = require_admin_permission("manage_admins")
    if err:
        return err, status

    conn = get_db_connection()
    if not conn:
        return jsonify({"success": False, "message": "Database connection failed"}), 500

    cursor = conn.cursor(dictionary=True)
    try:
        ensure_admin_role_overrides_table(cursor)

        if table_exists(cursor, "admin_credentials"):
            cursor.execute(
                """
                SELECT u.user_id, u.name, u.email, ac.active
                FROM admin_credentials ac
                LEFT JOIN users u ON u.email = ac.email
                WHERE ac.active = TRUE
                ORDER BY ac.email
                """
            )
            rows = cursor.fetchall()
        else:
            cursor.execute("SELECT user_id, name, email, is_admin FROM users WHERE is_admin=TRUE ORDER BY email")
            rows = cursor.fetchall()

        for row in rows:
            row["role"] = get_admin_role(cursor, row.get("email"), row.get("user_id"))
            row["permissions"] = sorted(list(ROLE_PERMISSIONS.get(row["role"], set())))
        return jsonify({"success": True, "admins": rows})
    finally:
        cursor.close()
        conn.close()


@admin_bp.route("/console/admin-users/<int:user_id>/role", methods=["PUT"])
def console_set_admin_role(user_id):
    _, err, status = require_admin_permission("manage_admins")
    if err:
        return err, status

    data = request.get_json() or {}
    role = (data.get("role") or "").strip()
    if role not in ROLE_PERMISSIONS:
        return jsonify({"success": False, "message": "Invalid role"}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({"success": False, "message": "Database connection failed"}), 500

    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT user_id, email FROM users WHERE user_id=%s", (user_id,))
        user = cursor.fetchone()
        if not user:
            return jsonify({"success": False, "message": "User not found"}), 404

        ensure_admin_role_overrides_table(cursor)
        cursor.execute(
            """
            INSERT INTO admin_role_overrides (email, role)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE role=VALUES(role)
            """,
            (user["email"], role),
        )
        conn.commit()
        log_admin_action("ADMIN_ROLE_UPDATED", "user", user_id, {"email": user["email"], "role": role})
        return jsonify({"success": True, "message": "Admin role updated"})
    finally:
        cursor.close()
        conn.close()


@admin_bp.route("/console/notifications/broadcast", methods=["POST"])
def console_broadcast_notification():
    _, err, status = require_admin_permission("manage_notifications")
    if err:
        return err, status

    data = request.get_json() or {}
    title = (data.get("title") or "").strip()
    message = (data.get("message") or "").strip()
    notif_type = (data.get("type") or "admin").strip()
    target = (data.get("target") or "all").strip()
    user_ids = data.get("user_ids") or []

    if not title or not message:
        return jsonify({"success": False, "message": "title and message are required"}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({"success": False, "message": "Database connection failed"}), 500

    cursor = conn.cursor(dictionary=True)
    try:
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
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        if target == "all":
            cursor.execute("SELECT user_id FROM users")
            recipients = [r["user_id"] for r in cursor.fetchall()]
        else:
            recipients = [int(x) for x in user_ids if str(x).isdigit()]

        if not recipients:
            return jsonify({"success": False, "message": "No recipients found"}), 400

        rows = [(uid, title, message, notif_type) for uid in recipients]
        cursor.executemany(
            "INSERT INTO notifications (user_id, title, message, type) VALUES (%s, %s, %s, %s)",
            rows
        )
        conn.commit()
        log_admin_action("NOTIFICATION_BROADCAST", "notification", None, {"target": target, "count": len(recipients), "title": title})
        return jsonify({"success": True, "sent": len(recipients)})
    finally:
        cursor.close()
        conn.close()


@admin_bp.route("/console/audit", methods=["GET"])
def console_audit_logs():
    _, err, status = require_admin_permission("view_audit")
    if err:
        return err, status

    limit = request.args.get("limit", 200, type=int)
    limit = max(1, min(limit, 1000))

    conn = get_db_connection()
    if not conn:
        return jsonify({"success": False, "message": "Database connection failed"}), 500
    cursor = conn.cursor(dictionary=True)
    try:
        ensure_admin_audit_logs_table(cursor)
        cursor.execute(
            """
            SELECT log_id, admin_user_id, admin_email, admin_role, action, entity_type, entity_id, details, created_at
            FROM admin_audit_logs
            ORDER BY created_at DESC
            LIMIT %s
            """,
            (limit,),
        )
        rows = cursor.fetchall()
        for row in rows:
            row["created_at"] = str(row["created_at"]) if row.get("created_at") else None
        return jsonify({"success": True, "logs": rows})
    finally:
        cursor.close()
        conn.close()


def _fetch_table_snapshot(cursor, table_name, order_by=None):
    if not table_exists(cursor, table_name):
        return []
    sql = f"SELECT * FROM {table_name}"
    if order_by:
        sql += f" ORDER BY {order_by}"
    cursor.execute(sql)
    rows = cursor.fetchall()
    for row in rows:
        for key, value in list(row.items()):
            if isinstance(value, (datetime, )):
                row[key] = value.isoformat()
            elif hasattr(value, "isoformat"):
                row[key] = value.isoformat()
    return rows


@admin_bp.route("/console/backup/export", methods=["GET"])
def console_backup_export():
    _, err, status = require_admin_permission("manage_backup")
    if err:
        return err, status

    conn = get_db_connection()
    if not conn:
        return jsonify({"success": False, "message": "Database connection failed"}), 500
    cursor = conn.cursor(dictionary=True)
    try:
        ensure_admin_role_overrides_table(cursor)
        ensure_admin_audit_logs_table(cursor)
        payload = {
            "exported_at": datetime.utcnow().isoformat() + "Z",
            "schema": "priorityiq-backup-v1",
            "tables": {
                "users": _fetch_table_snapshot(cursor, "users", "user_id"),
                "tasks": _fetch_table_snapshot(cursor, "tasks", "task_id"),
                "admin_credentials": _fetch_table_snapshot(cursor, "admin_credentials", "admin_id"),
                "notifications": _fetch_table_snapshot(cursor, "notifications", "notification_id"),
                "admin_role_overrides": _fetch_table_snapshot(cursor, "admin_role_overrides", "email"),
            },
        }
        blob = json.dumps(payload, indent=2).encode("utf-8")
        log_admin_action("BACKUP_EXPORTED", "backup", None, {"size_bytes": len(blob)})
        return send_file(
            io.BytesIO(blob),
            mimetype="application/json",
            as_attachment=True,
            download_name=f"priorityiq_backup_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json",
        )
    finally:
        cursor.close()
        conn.close()


def _restore_table(cursor, table_name, rows, mode):
    if not rows:
        return 0
    if not table_exists(cursor, table_name):
        return 0
    if mode == "replace":
        cursor.execute(f"DELETE FROM {table_name}")
    columns = list(rows[0].keys())
    placeholders = ", ".join(["%s"] * len(columns))
    column_clause = ", ".join(columns)
    updates = ", ".join([f"{c}=VALUES({c})" for c in columns])
    sql = f"INSERT INTO {table_name} ({column_clause}) VALUES ({placeholders}) ON DUPLICATE KEY UPDATE {updates}"
    values = [[row.get(col) for col in columns] for row in rows]
    cursor.executemany(sql, values)
    return cursor.rowcount


@admin_bp.route("/console/backup/restore", methods=["POST"])
def console_backup_restore():
    _, err, status = require_admin_permission("manage_backup")
    if err:
        return err, status

    data = request.get_json() or {}
    snapshot = data.get("snapshot") or {}
    mode = (data.get("mode") or "append").strip()
    if mode not in {"append", "replace"}:
        return jsonify({"success": False, "message": "mode must be append or replace"}), 400

    tables = snapshot.get("tables")
    if not isinstance(tables, dict):
        return jsonify({"success": False, "message": "snapshot.tables is required"}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({"success": False, "message": "Database connection failed"}), 500
    cursor = conn.cursor()
    try:
        ensure_admin_role_overrides_table(cursor)
        ensure_admin_audit_logs_table(cursor)

        restore_order = ["users", "tasks", "admin_credentials", "notifications", "admin_role_overrides"]
        if mode == "replace":
            cursor.execute("SET FOREIGN_KEY_CHECKS=0")
        affected = 0
        for table_name in restore_order:
            table_rows = tables.get(table_name) or []
            if isinstance(table_rows, list):
                affected += _restore_table(cursor, table_name, table_rows, mode)
        if mode == "replace":
            cursor.execute("SET FOREIGN_KEY_CHECKS=1")
        conn.commit()
        log_admin_action("BACKUP_RESTORED", "backup", None, {"mode": mode, "affected": affected})
        return jsonify({"success": True, "affected": affected})
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": f"Restore failed: {str(e)}"}), 500
    finally:
        cursor.close()
        conn.close()
