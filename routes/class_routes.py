from flask import Blueprint, request, jsonify, session
from db_connection import get_db_connection
import secrets
import string

class_bp = Blueprint("class_bp", __name__)

CODE_ALPHABET = string.ascii_uppercase + string.digits

def require_login():
    return "user_id" in session

def generate_code(length=6):
    return "".join(secrets.choice(CODE_ALPHABET) for _ in range(length))

def get_unique_code(cursor, attempts=12):
    for _ in range(attempts):
        code = generate_code()
        cursor.execute("SELECT class_id FROM classrooms WHERE code=%s", (code,))
        if not cursor.fetchone():
            return code
    return None

@class_bp.route("/create", methods=["POST"])
def create_class():
    try:
        if not require_login():
            return jsonify({"message": "Unauthorized"}), 401

        data = request.get_json() or {}
        name = (data.get("name") or "").strip()
        if not name:
            return jsonify({"message": "Class name is required"}), 400

        user_id = session.get("user_id")
        conn = get_db_connection()
        if not conn:
            return jsonify({"message": "DB connection failed"}), 500

        cursor = conn.cursor(dictionary=True)
        code = get_unique_code(cursor)
        if not code:
            cursor.close()
            conn.close()
            return jsonify({"message": "Failed to generate class code"}), 500

        cursor.execute(
            """
            INSERT INTO classrooms (name, code, owner_user_id)
            VALUES (%s, %s, %s)
            """,
            (name, code, user_id),
        )
        class_id = cursor.lastrowid

        cursor.execute(
            """
            INSERT INTO class_memberships (class_id, user_id, role)
            VALUES (%s, %s, %s)
            """,
            (class_id, user_id, "owner"),
        )

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"message": "Class created", "class_id": class_id, "code": code}), 201

    except Exception as e:
        print(f"Exception in create_class: {e}")
        return jsonify({"message": "Server error"}), 500

@class_bp.route("/join", methods=["POST"])
def join_class():
    try:
        if not require_login():
            return jsonify({"message": "Unauthorized"}), 401

        data = request.get_json() or {}
        code = (data.get("code") or "").strip().upper()
        if not code:
            return jsonify({"message": "Join code is required"}), 400

        user_id = session.get("user_id")
        conn = get_db_connection()
        if not conn:
            return jsonify({"message": "DB connection failed"}), 500

        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT class_id, name FROM classrooms WHERE code=%s", (code,))
        classroom = cursor.fetchone()
        if not classroom:
            cursor.close()
            conn.close()
            return jsonify({"message": "Invalid class code"}), 404

        cursor.execute(
            """
            SELECT membership_id FROM class_memberships
            WHERE class_id=%s AND user_id=%s
            """,
            (classroom["class_id"], user_id),
        )
        if cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({"message": "You are already in this class"}), 200

        cursor.execute(
            """
            INSERT INTO class_memberships (class_id, user_id, role)
            VALUES (%s, %s, %s)
            """,
            (classroom["class_id"], user_id, "member"),
        )
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"message": "Joined class", "class_id": classroom["class_id"]}), 201

    except Exception as e:
        print(f"Exception in join_class: {e}")
        return jsonify({"message": "Server error"}), 500

@class_bp.route("/my", methods=["GET"])
def my_classes():
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
            SELECT c.class_id, c.name, c.code, c.owner_user_id, c.created_at,
                   m.role, u.name AS owner_name
            FROM class_memberships m
            JOIN classrooms c ON c.class_id = m.class_id
            LEFT JOIN users u ON u.user_id = c.owner_user_id
            WHERE m.user_id=%s
            ORDER BY c.created_at DESC
            """,
            (user_id,),
        )
        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        for row in rows:
            row["created_at"] = str(row["created_at"]) if row.get("created_at") else None

        return jsonify({"classes": rows}), 200
    except Exception as e:
        print(f"Exception in my_classes: {e}")
        return jsonify({"message": "Server error"}), 500

@class_bp.route("/leave", methods=["POST"])
def leave_class():
    try:
        if not require_login():
            return jsonify({"message": "Unauthorized"}), 401

        data = request.get_json() or {}
        class_id = data.get("class_id")
        if not class_id:
            return jsonify({"message": "class_id is required"}), 400

        user_id = session.get("user_id")
        conn = get_db_connection()
        if not conn:
            return jsonify({"message": "DB connection failed"}), 500

        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT role FROM class_memberships
            WHERE class_id=%s AND user_id=%s
            """,
            (class_id, user_id),
        )
        membership = cursor.fetchone()
        if not membership:
            cursor.close()
            conn.close()
            return jsonify({"message": "Not a member of this class"}), 404

        if membership.get("role") == "owner":
            cursor.close()
            conn.close()
            return jsonify({"message": "Owner cannot leave their own class"}), 400

        cursor.execute(
            "DELETE FROM class_memberships WHERE class_id=%s AND user_id=%s",
            (class_id, user_id),
        )
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"message": "Left class"}), 200
    except Exception as e:
        print(f"Exception in leave_class: {e}")
        return jsonify({"message": "Server error"}), 500
