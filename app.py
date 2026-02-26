from flask import Flask, render_template, session, redirect, send_from_directory
from routes.auth_routes import auth_bp
from routes.task_routes import task_bp
from routes.predict_routes import predict_bp
from routes.chatbot_routes import chatbot_bp
from routes.gamify_routes import gamify_bp
from routes.history_routes import history_bp
from routes.admin_routes import admin_bp, is_admin as is_admin_user
import os
from dotenv import load_dotenv
import secrets

# Import email reminder service
try:
    from email_reminders import start_email_scheduler
    EMAIL_ENABLED = True
except ImportError:
    EMAIL_ENABLED = False
    print("Email reminders disabled (missing dependencies)")

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", secrets.token_hex(32))
app.config['SESSION_COOKIE_SECURE'] = os.getenv("FLASK_ENV") != "development"
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(task_bp, url_prefix='/api/tasks')
app.register_blueprint(predict_bp, url_prefix='/api/predict')
app.register_blueprint(chatbot_bp, url_prefix='/api/chatbot')
app.register_blueprint(gamify_bp, url_prefix='/api/gamify')
app.register_blueprint(history_bp, url_prefix='/api/history')
app.register_blueprint(admin_bp, url_prefix='/api/admin')

def login_required():
    return "user_id" in session

def is_admin():
    return is_admin_user()

@app.route("/")
def index():
    if not login_required():
        return redirect("/login")
    if is_admin():
        return redirect("/admin-dashboard")
    return render_template("index.html")

@app.route("/add")
def add_task():
    if not login_required():
        return redirect("/login")
    return render_template("add_task.html")

@app.route("/analytics")
def analytics():
    if not login_required():
        return redirect("/login")
    return render_template("analytics.html")

@app.route("/calendar")
def calendar():
    if not login_required():
        return redirect("/login")
    return render_template("calendar.html")

@app.route("/kanban")
def kanban():
    if not login_required():
        return redirect("/login")
    return render_template("kanban.html")

@app.route("/history")
def history():
    if not login_required():
        return redirect("/login")
    return render_template("history.html")

@app.route("/login")
def login_page():
    return render_template("login.html")

@app.route("/admin-login")
def admin_login_page():
    return render_template("admin_login.html")

@app.route("/register")
def register_page():
    return render_template("register.html")

@app.route("/verify-otp")
def verify_otp_page():
    return render_template("verify_otp.html")

@app.route("/face-verify")
def face_verify_page():
    return render_template("face_verify.html")

@app.route("/admin")
def admin_page():
    if not login_required():
        return redirect("/login")
    if not is_admin():
        return redirect("/")
    return redirect("/admin-dashboard")

@app.route("/admin-dashboard")
def admin_dashboard():
    if not login_required():
        return redirect("/admin-login")
    if not is_admin():
        return redirect("/")
    return render_template("admin_dashboard.html")

@app.route('/manifest.json')
def manifest():
    return send_from_directory('static', 'manifest.json', mimetype='application/manifest+json')

@app.route('/service-worker.js')
def service_worker():
    return send_from_directory('static', 'service-worker.js', mimetype='application/javascript')

if __name__ == "__main__":
    debug_mode = os.getenv("FLASK_ENV") == "development"
    
    # Start email reminder service
    if EMAIL_ENABLED:
        start_email_scheduler()
    
    app.run(debug=debug_mode, host="0.0.0.0", port=5000)
