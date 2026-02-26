from flask import Blueprint, jsonify, session
from db_connection import get_db_connection
from datetime import date

gamify_bp = Blueprint('gamify_bp', __name__)

@gamify_bp.route('/stats', methods=['GET'])
def get_gamification_stats():
    if 'user_id' not in session:
        return jsonify({'message': 'Unauthorized'}), 401
    
    user_id = session['user_id']
    conn = get_db_connection()
    if not conn:
        return jsonify({'message': 'DB connection failed'}), 500
    
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT points, streak, badges FROM users WHERE user_id=%s", (user_id,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if not user:
        return jsonify({'message': 'User not found'}), 404
    
    badges_list = user['badges'].split(',') if user['badges'] else []
    
    return jsonify({
        'points': user['points'] or 0,
        'streak': user['streak'] or 0,
        'badges': badges_list,
        'level': (user['points'] or 0) // 100 + 1
    })
