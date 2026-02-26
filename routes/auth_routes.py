from flask import Blueprint, request, session, jsonify
import secrets
from db_connection import get_db_connection
import json
from datetime import datetime, timedelta

auth_bp = Blueprint('auth_bp', __name__)

ALLOWED_LOGIN_TYPES = {"student", "admin"}

def admin_table_exists(cursor):
    cursor.execute("SHOW TABLES LIKE %s", ("admin_credentials",))
    return cursor.fetchone() is not None

def clear_otp_session():
    session.pop("otp", None)
    session.pop("otp_expires_at", None)
    session.pop("otp_attempts", None)

@auth_bp.route("/register", methods=["POST"])
def register():
    try:
        data = request.json
        if not data:
            return jsonify({"success": False, "message": "Invalid request"}), 400
        
        name = data.get("name", "").strip()
        email = data.get("email", "").strip()
        phone = data.get("phone", "").strip()
        role = data.get("role", "").strip()
        age = data.get("age")
        gender = data.get("gender", "").strip()

        # Validation
        if not name or not email or not phone:
            return jsonify({"success": False, "message": "Name, email, and phone are required"}), 400
        
        if "@" not in email:
            return jsonify({"success": False, "message": "Invalid email format"}), 400
        
        if not phone.isdigit() or len(phone) < 10:
            return jsonify({"success": False, "message": "Invalid phone number"}), 400
        
        try:
            age = int(age) if age else None
            if age and (age < 13 or age > 120):
                return jsonify({"success": False, "message": "Invalid age"}), 400
        except (ValueError, TypeError):
            age = None

        conn = get_db_connection()
        if not conn:
            return jsonify({"success": False, "message": "Database connection failed"}), 500
        
        cursor = conn.cursor(dictionary=True)
        
        # Check if email already exists
        cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({"success": False, "message": "Email already registered"}), 400
        
        # Check if phone already exists (only if phone is not null)
        cursor.execute("SELECT * FROM users WHERE phone=%s AND phone IS NOT NULL", (phone,))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({"success": False, "message": "Phone number already registered"}), 400
        
        # Public registration must never grant admin access directly.
        is_admin = False
        safe_role = None if role.lower() == "admin" else (role if role else None)
        cursor.execute(
            "INSERT INTO users (name, email, phone, role, age, gender, password, is_admin) VALUES (%s, %s, %s, %s, %s, %s, '', %s)",
            (name, email, phone, safe_role, age, gender if gender else None, is_admin)
        )
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"success": True, "message": "Registration successful! Please login."}), 201

    except Exception as e:
        print(f"Error in register: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "message": "Server error"}), 500

@auth_bp.route("/request_otp", methods=["POST"])
def request_otp():
    try:
        data = request.json
        if not data:
            return jsonify({"success": False, "message": "Invalid request"}), 400
        
        email = data.get("email", "").strip()
        login_type = data.get("login_type", "student")
        if login_type not in ALLOWED_LOGIN_TYPES:
            return jsonify({"success": False, "message": "Invalid login type"}), 400

        if not email or "@" not in email:
            return jsonify({"success": False, "message": "Valid email is required"}), 400

        conn = get_db_connection()
        if not conn:
            return jsonify({"success": False, "message": "Database connection failed"}), 500
        
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cursor.fetchone()

        if not user:
            cursor.close()
            conn.close()
            return jsonify({"success": False, "message": "Email not registered. Please register first."}), 404

        # Check if user type matches login type (admin credentials live in admin_credentials)
        if admin_table_exists(cursor):
            cursor.execute(
                "SELECT 1 FROM admin_credentials WHERE email=%s AND active=TRUE",
                (email,)
            )
            is_admin_credential = cursor.fetchone() is not None
        else:
            is_admin_credential = user.get("is_admin", False)

        if login_type == "admin" and not is_admin_credential:
            cursor.close()
            conn.close()
            return jsonify({"success": False, "message": "Access denied. Admin credentials required."}), 403
        if login_type == "student" and is_admin_credential:
            cursor.close()
            conn.close()
            return jsonify({"success": False, "message": "Please use admin login."}), 403

        cursor.close()
        conn.close()

        # Generate OTP
        otp = secrets.randbelow(900000) + 100000
        session["otp"] = otp
        session["email"] = email
        session["login_type"] = login_type
        session["otp_expires_at"] = (datetime.utcnow() + timedelta(minutes=5)).isoformat()
        session["otp_attempts"] = 0

        print(f"OTP generated for {email} ({login_type})")

        return jsonify({
            "success": True,
            "message": "OTP generated successfully",
            "otp": str(otp)
        })
    except Exception as e:
        print(f"Error in request_otp: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "message": "Server error"}), 500

@auth_bp.route("/verify_otp", methods=["POST"])
def verify_otp():
    try:
        data = request.json
        if not data:
            return jsonify({"success": False, "message": "Invalid request"}), 400
        
        entered_otp = data.get("otp")
        if not entered_otp:
            return jsonify({"success": False, "message": "OTP is required"}), 400
        
        try:
            entered_otp = int(entered_otp)
        except ValueError:
            return jsonify({"success": False, "message": "Invalid OTP format"}), 400
        
        real_otp = session.get("otp")
        email = session.get("email")
        expires_at = session.get("otp_expires_at")
        attempts = int(session.get("otp_attempts", 0))
        login_type = session.get("login_type", "student")

        if not real_otp or not email:
            return jsonify({"success": False, "message": "Session expired. Please request OTP again."}), 400

        if attempts >= 5:
            clear_otp_session()
            return jsonify({"success": False, "message": "Too many OTP attempts. Request a new OTP."}), 429

        if expires_at:
            try:
                if datetime.utcnow() > datetime.fromisoformat(expires_at):
                    clear_otp_session()
                    return jsonify({"success": False, "message": "OTP expired. Request a new OTP."}), 400
            except ValueError:
                clear_otp_session()
                return jsonify({"success": False, "message": "Session expired. Please request OTP again."}), 400

        if entered_otp == real_otp:
            conn = get_db_connection()
            if not conn:
                return jsonify({"success": False, "message": "Database connection failed"}), 500
            
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
            user = cursor.fetchone()

            if user:
                if admin_table_exists(cursor):
                    cursor.execute(
                        "SELECT 1 FROM admin_credentials WHERE email=%s AND active=TRUE",
                        (email,)
                    )
                    is_admin_credential = cursor.fetchone() is not None
                else:
                    is_admin_credential = user.get("is_admin", False)

                if login_type == "admin" and not is_admin_credential:
                    cursor.close()
                    conn.close()
                    return jsonify({"success": False, "message": "Access denied. Admin credentials required."}), 403
                if login_type == "student" and is_admin_credential:
                    cursor.close()
                    conn.close()
                    return jsonify({"success": False, "message": "Please use admin login."}), 403

                session["user_id"] = user["user_id"]
                session["user_name"] = user["name"]
                session["email"] = email
                clear_otp_session()
                cursor.close()
                conn.close()
                return jsonify({"success": True, "message": "Login successful"})
            cursor.close()
            conn.close()

        session["otp_attempts"] = attempts + 1
        return jsonify({"success": False, "message": "Invalid OTP"}), 401
    except Exception as e:
        print(f"Error in verify_otp: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "message": "Server error"}), 500

@auth_bp.route("/status")
def auth_status():
    if "user_id" in session:
        return jsonify({
            "logged_in": True, 
            "email": session.get("email"),
            "name": session.get("user_name")
        })
    return jsonify({"logged_in": False})

@auth_bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"success": True})

@auth_bp.route("/verify_face", methods=["POST"])
def verify_face():
    try:
        data = request.json
        if not data:
            return jsonify({"success": False, "message": "Invalid request"}), 400
        
        email = data.get("email", "").strip()
        face_descriptor = data.get("faceDescriptor")
        
        if not email or not face_descriptor:
            return jsonify({"success": False, "message": "Email and face data required"}), 400

        # Face verification is only valid after OTP/login flow for this same session/email.
        if "user_id" not in session or session.get("email") != email:
            return jsonify({"success": False, "message": "Unauthorized face verification request"}), 401
        
        conn = get_db_connection()
        if not conn:
            return jsonify({"success": False, "message": "Database connection failed"}), 500
        
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cursor.fetchone()
        
        if not user:
            cursor.close()
            conn.close()
            return jsonify({"success": False, "message": "User not found"}), 404
        
        face_data = user.get('face_data')
        
        # First time face registration
        if not face_data:
            try:
                cursor.execute(
                    "UPDATE users SET face_data=%s WHERE email=%s",
                    (json.dumps(face_descriptor), email)
                )
                conn.commit()
            except Exception as e:
                print(f"Face data save error: {e}")
            
            cursor.close()
            conn.close()
            
            # Log user in
            session["user_id"] = user["user_id"]
            session["user_name"] = user["name"]
            session["email"] = email
            
            return jsonify({
                "success": True, 
                "message": "Face registered successfully",
                "first_time": True
            })
        
        # Verify against stored face
        try:
            import numpy as np
            stored_descriptor = json.loads(face_data)
            
            # Calculate Euclidean distance for THIS user
            distance = np.linalg.norm(
                np.array(face_descriptor) - np.array(stored_descriptor)
            )
            
            # Check if this face matches ANY OTHER user (prevent face reuse)
            cursor.execute("SELECT user_id, face_data FROM users WHERE face_data IS NOT NULL AND email != %s", (email,))
            other_users = cursor.fetchall()
            
            for other_user in other_users:
                try:
                    other_face_data = other_user.get('face_data')
                    if other_face_data:
                        other_descriptor = json.loads(other_face_data)
                        other_distance = np.linalg.norm(
                            np.array(face_descriptor) - np.array(other_descriptor)
                        )
                        # If face matches another user, reject
                        if other_distance < 0.6:
                            cursor.close()
                            conn.close()
                            return jsonify({
                                "success": False,
                                "message": "This face is already registered to another user. Please use your own face."
                            }), 403
                except Exception as e:
                    print(f"Error checking other user: {e}")
                    continue
            
            # Threshold for face match
            THRESHOLD = 0.6
            
            cursor.close()
            conn.close()
            
            if distance < THRESHOLD:
                # Face matched - log user in
                session["user_id"] = user["user_id"]
                session["user_name"] = user["name"]
                session["email"] = email
                
                return jsonify({
                    "success": True,
                    "message": "Face verified successfully",
                    "confidence": round((1 - distance) * 100, 2)
                })
            else:
                return jsonify({
                    "success": False,
                    "message": "Face does not match. Please try again or skip.",
                    "confidence": round((1 - distance) * 100, 2)
                }), 401
        
        except ImportError:
            cursor.close()
            conn.close()
            return jsonify({
                "success": False,
                "message": "Face verification service unavailable"
            }), 503
    
    except Exception as e:
        print(f"Error in verify_face: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "message": f"Server error: {str(e)}"}), 500
