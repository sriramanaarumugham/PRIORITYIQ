from flask import Blueprint, request, jsonify
import pickle
import os
from db_connection import get_db_connection
from datetime import datetime

predict_bp = Blueprint("predict_bp", __name__)

MODEL_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "ml", "model.pkl")

try:
    with open(MODEL_PATH, "rb") as f:
        model = pickle.load(f)
except Exception as e:
    model = None
    print(f"Model load error: {e}")

LABEL_MAP = {2: "High", 1: "Medium", 0: "Low"}

@predict_bp.route("/quick", methods=["POST"])
def predict_quick():
    if model is None:
        return jsonify({"message":"Model not available. Run train_model.py first."}), 500

    try:
        data = request.json
        if not data:
            return jsonify({"message":"Invalid request data"}), 400
        
        try:
            urgency = float(data.get("urgency", 1))
            complexity = float(data.get("complexity", 1))
            est_hours = float(data.get("est_hours", 1))
            
            deadline_str = data.get("deadline")
            if deadline_str:
                deadline_date = datetime.strptime(deadline_str, "%Y-%m-%d")
                deadline_days = (deadline_date - datetime.now()).days
            else:
                deadline_days = 7
        except (ValueError, TypeError) as e:
            return jsonify({"message":f"Invalid input values: {e}"}), 400

        features = [[urgency, complexity, est_hours, deadline_days]]
        pred_label = model.predict(features)[0]
        pred_str = LABEL_MAP.get(int(pred_label), "Low")

        return jsonify({"predicted_priority": pred_str}), 200
    except Exception as e:
        print(f"Error in predict_quick: {e}")
        return jsonify({"message":"Server error"}), 500

@predict_bp.route("/priority", methods=["POST"])
def predict_priority():
    if model is None:
        return jsonify({"message":"Model not available. Run train_model.py first."}), 500

    try:
        data = request.json
        if not data:
            return jsonify({"message":"Invalid request data"}), 400
        
        try:
            urgency = float(data.get("urgency", 1))
            complexity = float(data.get("complexity", 1))
            est_hours = float(data.get("est_hours", 1))
            deadline_days = float(data.get("deadline_days", 7))
        except (ValueError, TypeError):
            return jsonify({"message":"Invalid numeric values"}), 400

        features = [[urgency, complexity, est_hours, deadline_days]]
        pred_label = model.predict(features)[0]
        pred_str = LABEL_MAP.get(int(pred_label), "Low")

        task_id = data.get("task_id")
        if task_id:
            conn = get_db_connection()
            if conn:
                try:
                    cursor = conn.cursor()
                    cursor.execute(
                        "INSERT INTO priority_predictions (task_id, predicted_priority, model_version) VALUES (%s,%s,%s)",
                        (task_id, pred_str, "v1")
                    )
                    conn.commit()
                    cursor.close()
                except Exception as e:
                    print(f"Error saving prediction: {e}")
                finally:
                    conn.close()

        return jsonify({"predicted_priority": pred_str}), 200
    except Exception as e:
        print(f"Error in predict_priority: {e}")
        return jsonify({"message":"Server error"}), 500

@predict_bp.route("/risk", methods=["GET"])
def deadline_risk():
    try:
        from flask import session
        if 'user_id' not in session:
            return jsonify({"message":"Unauthorized"}), 401

        user_id = session.get("user_id")
        conn = get_db_connection()
        if not conn:
            return jsonify({"message":"DB connection failed"}), 500

        cursor = conn.cursor(dictionary=True)
        
        # Get tasks at risk (incomplete, deadline within 3 days)
        cursor.execute("""
            SELECT task_id, title, deadline, priority_level, urgency, complexity,
                   DATEDIFF(deadline, CURDATE()) as days_left
            FROM tasks 
            WHERE user_id=%s AND status != 'Completed'
            AND deadline >= CURDATE()
            ORDER BY deadline ASC
        """, (user_id,))
        
        tasks = cursor.fetchall()
        cursor.close()
        conn.close()
        
        risk_tasks = []
        for task in tasks:
            days_left = task["days_left"]
            risk_level = "Low"
            
            if days_left <= 1:
                risk_level = "Critical"
            elif days_left <= 3:
                risk_level = "High"
            elif days_left <= 7:
                risk_level = "Medium"
            
            risk_tasks.append({
                "task_id": task["task_id"],
                "title": task["title"],
                "deadline": str(task["deadline"]),
                "days_left": days_left,
                "risk_level": risk_level,
                "priority": task["priority_level"]
            })
        
        return jsonify({"at_risk_tasks": risk_tasks}), 200

    except Exception as e:
        print(f"Error in deadline_risk: {e}")
        return jsonify({"message":"Server error"}), 500
