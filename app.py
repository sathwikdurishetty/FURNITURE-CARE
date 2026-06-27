import os
import sqlite3
import json
import requests
import shutil
from dotenv import load_dotenv
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
CORS(app)

DB_FILE = 'furniture_care.db'

# Check if running in Vercel serverless environment
if os.environ.get('VERCEL'):
    tmp_db = '/tmp/furniture_care.db'
    if not os.path.exists(tmp_db):
        if os.path.exists('furniture_care.db'):
            try:
                shutil.copy('furniture_care.db', tmp_db)
            except Exception as e:
                print(f"Error copying database: {e}")
    DB_FILE = tmp_db

GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    print("Warning: GEMINI_API_KEY environment variable is not set. Please configure it in your .env file.")

# Initialize SQLite database
def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            full_name TEXT NOT NULL,
            phone TEXT,
            role TEXT DEFAULT 'user',
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create Guides table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS guides (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            user_name TEXT,
            furniture_name TEXT NOT NULL,
            furniture_type TEXT NOT NULL,
            material TEXT NOT NULL,
            brand TEXT,
            age TEXT,
            indoor_outdoor TEXT,
            condition TEXT NOT NULL,
            problem_description TEXT,
            image_url TEXT,
            report_json TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Insert default admin user if not exists
    cursor.execute('SELECT * FROM users WHERE username = ?', ('8309035966',))
    admin = cursor.fetchone()
    if not admin:
        cursor.execute('''
            INSERT INTO users (username, password, full_name, phone, role, status)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', ('8309035966', 'admin@12', 'System Administrator', '8309035966', 'admin', 'approved'))
        
    conn.commit()
    conn.close()

init_db()

# Prefills API
@app.route('/api/prefills', methods=['GET'])
def get_prefills():
    prefills = {
        'furnitureTypes': ["Sofa / Couch", "Dining Table", "Armchair", "Bed Frame", "Coffee Table", "Bookshelf / Cabinet", "Office Chair", "Patio Lounger"],
        'materials': ["Solid Wood", "Veneer / Engineered Wood", "Genuine Leather", "Vegan Leather / PU", "Fabric (Cotton/Linen)", "Fabric (Velvet)", "Metal (Steel/Aluminium)", "Marble / Stone", "Rattan / Wicker"],
        'brands': ["West Elm", "IKEA", "Pottery Barn", "Crate & Barrel", "Herman Miller", "Restoration Hardware", "Ashley Furniture", "Custom / Unbranded"],
        'ages': ["Brand New (< 1 year)", "Recently Purchased (1-3 years)", "Well Used (3-7 years)", "Vintage (7-15 years)", "Antique (15+ years)"],
        'conditions': ["Excellent (No wear)", "Good (Minor scratches/fading)", "Fair (Visible stains/wear)", "Poor (Structural issues/deep stains)"]
    }
    return jsonify(prefills)

# Authentication APIs
@app.route('/api/auth/signup', methods=['POST'])
def signup():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    full_name = data.get('fullName')
    phone = data.get('phone', '')

    if not username or not password or not full_name:
        return jsonify({ 'error': 'Username, password, and full name are required.' }), 400

    if username == '8309035966':
        return jsonify({ 'error': 'This username is reserved for system administration.' }), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO users (username, password, full_name, phone, role, status)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (username, password, full_name, phone, 'user', 'pending'))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({ 'error': 'Username already exists.' }), 400

    conn.close()
    return jsonify({
        'message': 'Registration successful! Your account is pending admin approval.',
        'status': 'pending'
    }), 201

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({ 'error': 'Username and password are required.' }), 400

    # Explicit check for admin
    if username == '8309035966' and password == 'admin@12':
        return jsonify({
            'id': 'admin_sys',
            'username': '8309035966',
            'fullName': 'System Administrator',
            'role': 'admin',
            'status': 'approved'
        })

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password))
    user = cursor.fetchone()
    conn.close()

    if not user:
        return jsonify({ 'error': 'Invalid username or password.' }), 401

    if user['status'] == 'pending':
        return jsonify({ 'error': 'Your account is pending approval by the admin. Please try again later.' }), 403

    if user['status'] == 'rejected':
        return jsonify({ 'error': 'Your account registration was rejected by the admin.' }), 403

    return jsonify({
        'id': str(user['id']),
        'username': user['username'],
        'fullName': user['full_name'],
        'role': user['role'],
        'status': user['status']
    })

# Admin APIs
@app.route('/api/admin/users', methods=['GET'])
def admin_get_users():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, username, full_name, phone, role, status, created_at FROM users')
    users = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(users)

@app.route('/api/admin/users/approve', methods=['POST'])
def admin_approve_user():
    data = request.json
    user_id = data.get('userId')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET status = "approved" WHERE id = ?', (user_id,))
    conn.commit()
    conn.close()
    
    return jsonify({ 'message': 'User approved successfully.' })

@app.route('/api/admin/users/reject', methods=['POST'])
def admin_reject_user():
    data = request.json
    user_id = data.get('userId')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET status = "rejected" WHERE id = ?', (user_id,))
    conn.commit()
    conn.close()
    
    return jsonify({ 'message': 'User registration rejected.' })

# Guide Generation API via Gemini AI
@app.route('/api/guides/generate', methods=['POST'])
def generate_guide():
    data = request.json
    furniture_name = data.get('furnitureName')
    furniture_type = data.get('furnitureType')
    material = data.get('material')
    brand = data.get('brand', 'Generic')
    age = data.get('age', 'Brand New (< 1 year)')
    indoor_outdoor = data.get('indoorOutdoor', 'Indoor')
    condition = data.get('condition')
    problem_description = data.get('problemDescription', 'None')
    user_id = data.get('userId', 'anonymous')
    image_url = data.get('imageUrl', '')

    if not furniture_name or not furniture_type or not material or not condition:
        return jsonify({ 'error': 'Name, type, material, and condition are required.' }), 400

    # Fetch user full name for logging
    user_name = 'Anonymous User'
    if user_id != 'anonymous':
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT full_name FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        if user:
            user_name = user['full_name']
        conn.close()

    # Dynamic Gemini Prompt
    prompt = f"""
    You are an elite furniture restoration expert and material scientist.
    Generate a premium, detailed furniture care, cleaning, protection and maintenance report.
    The furniture details are:
    - Name: "{furniture_name}"
    - Type: "{furniture_type}"
    - Material: "{material}"
    - Brand: "{brand}"
    - Age: "{age}"
    - Location: "{indoor_outdoor}"
    - Current Condition: "{condition}"
    - Specific Problem/Issue: "{problem_description}"

    Respond with a strict JSON format containing these exact keys. Do not include markdown code block formatting (like ```json) or other text, just return the raw JSON object.
    
    JSON keys:
    {{
      "cleaningInstructions": [Array of 3-5 specific, step-by-step cleaning instructions for this material and brand],
      "maintenanceSchedule": [
        Array of 3 objects representing maintenance tasks. Each object must have "frequency" (e.g. "Weekly", "Every 6 Months") and "task" (detailed task description)
      ],
      "protectionRecommendations": [Array of 3-4 recommendations to protect this material based on location and age],
      "repairSuggestions": [Array of 2-3 specific suggestions to repair the listed problem or maintain stability],
      "dos": [Array of 3 specific things to do],
      "donts": [Array of 3 specific things to avoid],
      "estimatedCost": "A range in Indian Rupees like '₹1,500 - ₹4,000' representing expected annual care or repair cost",
      "healthScore": A number from 0 to 100 assessing the structural/cosmetic health based on condition and age,
      "detectedFurnitureType": "A short classification of the furniture category (e.g., Sofa, Dining Table)",
      "identifiedMaterial": "The exact identified material type (e.g., Solid Wood, Genuine Leather)",
      "detectedDamage": "A specific description of the surface damage or wear signs detected from the problem description and photo (e.g. water stains, leather cracking, wood scratches, or 'No surface damage detected')",
      "estimatedRepairCost": "A single estimated repair price in Indian Rupees (e.g. '₹2,500')",
      "estimatedReplacementCost": "A single estimated full replacement price in Indian Rupees (e.g. '₹28,000')",
      "yearlyMaintenanceCost": "Expected yearly maintenance expenses in Indian Rupees (e.g. '₹1,500')",
      "imageMatchStatus": A boolean (true or false). Check if the attached photo matches the described furniture category and material. If the photo content is unrelated (e.g., is a screenshot, face, animal, or mismatched furniture type), set to false. If no photo is attached, set to true.,
      "imageValidationMessage": "A warning string if imageMatchStatus is false (e.g., 'Warning: The uploaded image does not match the described Dining Table / Solid Wood. Please upload a correct photo.'), otherwise empty string ''"
    }}
    """

    ai_report = None

    # Setup parts array for multimodal query
    parts = [{"text": prompt}]
    if image_url and ";base64," in image_url:
        try:
            header, encoded = image_url.split(";base64,")
            mime_type = header.replace("data:", "")
            parts.append({
                "inline_data": {
                    "mime_type": mime_type,
                    "data": encoded
                }
            })
            print("Successfully attached image parts to Gemini API query payload.")
        except Exception as ex:
            print(f"Error parsing uploaded image: {str(ex)}")

    try:
        # Direct REST request to Gemini AI
        gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
        headers = { 'Content-Type': 'application/json' }
        payload = {
            "contents": [{
                "parts": parts
            }]
        }
        
        # 30s timeout
        response = requests.post(gemini_url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
       
        resp_json = response.json()
        raw_text = resp_json['candidates'][0]['content']['parts'][0]['text'].strip()
        
        # Strip potential markdown wrapper
        if raw_text.startswith('```'):
            raw_text = raw_text.replace('```json', '').replace('```', '').strip()
            
        ai_report = json.loads(raw_text)
    except Exception as e:
        print(f"Gemini API Error: {str(e)}.")
        return jsonify({ 'error': f"Gemini API Error: {str(e)}" }), 500

    # Save to SQLite
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO guides (user_id, user_name, furniture_name, furniture_type, material, brand, age, indoor_outdoor, condition, problem_description, image_url, report_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, user_name, furniture_name, furniture_type, material, brand, age, indoor_outdoor, condition, problem_description, image_url, json.dumps(ai_report)))
    
    new_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return jsonify({
        'id': str(new_id),
        'userId': user_id,
        'userName': user_name,
        'furnitureName': furniture_name,
        'furnitureType': furniture_type,
        'material': material,
        'brand': brand,
        'age': age,
        'indoorOutdoor': indoor_outdoor,
        'condition': condition,
        'problemDescription': problem_description,
        'imageUrl': image_url,
        'report': ai_report
    }), 201

# Guides retrieval and deletion APIs
@app.route('/api/guides', methods=['GET'])
def get_guides():
    user_id = request.args.get('userId')
    role = request.args.get('role')

    conn = get_db_connection()
    cursor = conn.cursor()

    if role == 'admin':
        cursor.execute('SELECT * FROM guides ORDER BY created_at DESC')
    else:
        cursor.execute('SELECT * FROM guides WHERE user_id = ? ORDER BY created_at DESC', (user_id or 'anonymous',))
        
    rows = cursor.fetchall()
    conn.close()

    guides = []
    for r in rows:
        guides.append({
            'id': str(r['id']),
            'userId': r['user_id'],
            'userName': r['user_name'],
            'furnitureName': r['furniture_name'],
            'furnitureType': r['furniture_type'],
            'material': r['material'],
            'brand': r['brand'],
            'age': r['age'],
            'indoorOutdoor': r['indoor_outdoor'],
            'condition': r['condition'],
            'problemDescription': r['problem_description'],
            'imageUrl': r['image_url'],
            'report': json.loads(r['report_json']),
            'createdAt': r['created_at']
        })
    return jsonify(guides)

@app.route('/api/guides/<int:guide_id>', methods=['GET'])
def get_guide_details(guide_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM guides WHERE id = ?', (guide_id,))
    r = cursor.fetchone()
    conn.close()

    if not r:
        return jsonify({ 'error': 'Guide not found.' }), 404

    return jsonify({
        'id': str(r['id']),
        'userId': r['user_id'],
        'userName': r['user_name'],
        'furnitureName': r['furniture_name'],
        'furnitureType': r['furniture_type'],
        'material': r['material'],
        'brand': r['brand'],
        'age': r['age'],
        'indoorOutdoor': r['indoor_outdoor'],
        'condition': r['condition'],
        'problemDescription': r['problem_description'],
        'imageUrl': r['image_url'],
        'report': json.loads(r['report_json']),
        'createdAt': r['created_at']
    })

@app.route('/api/guides/<int:guide_id>', methods=['DELETE'])
def delete_guide(guide_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM guides WHERE id = ?', (guide_id,))
    conn.commit()
    conn.close()
    return jsonify({ 'message': 'Report deleted successfully.' })

# Analytics API
@app.route('/api/analytics', methods=['GET'])
def get_analytics():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Total Reports
    cursor.execute('SELECT COUNT(*) as total FROM guides')
    total_reports = cursor.fetchone()['total']
    
    # Reports
    cursor.execute('SELECT report_json FROM guides')
    rows = cursor.fetchall()
    
    total_score = 0
    for r in rows:
        try:
            report_data = json.loads(r['report_json'])
            total_score += report_data.get('healthScore', 80)
        except Exception:
            total_score += 80
            
    avg_health = round(total_score / len(rows)) if rows else 100

    # Type distribution
    cursor.execute('SELECT furniture_type, COUNT(*) as count FROM guides GROUP BY furniture_type')
    type_dist = {r['furniture_type']: r['count'] for r in cursor.fetchall()}

    # Material distribution
    cursor.execute('SELECT material, COUNT(*) as count FROM guides GROUP BY material')
    mat_dist = {r['material']: r['count'] for r in cursor.fetchall()}

    # User metrics
    cursor.execute('SELECT COUNT(*) as total FROM users WHERE role = "user"')
    total_users = cursor.fetchone()['total']

    cursor.execute('SELECT COUNT(*) as total FROM users WHERE status = "pending"')
    pending_users = cursor.fetchone()['total']

    conn.close()

    return jsonify({
        'totalReports': total_reports,
        'avgHealth': avg_health,
        'furnitureDistribution': type_dist,
        'materialDistribution': mat_dist,
        'totalUsersCount': total_users,
        'pendingUsersCount': pending_users
    })

# Interactive AI Chatbot Endpoint
@app.route('/api/chat', methods=['POST'])
def chat_bot():
    data = request.json
    message = data.get('message')
    report_id = data.get('reportId')
    
    if not message:
        return jsonify({ 'error': 'Message is required.' }), 400
        
    # Greet user instantly if message is a simple greeting
    clean_msg = message.strip().lower()
    if clean_msg in ['hey', 'hi', 'hello', 'hey aura', 'hello aura', 'hi aura']:
        return jsonify({ 'response': "Hello! How can AURA AI assist you today with your furniture assets?" })
        
    context = ""
    if report_id:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT furniture_name, furniture_type, material, brand, age, condition, problem_description, report_json FROM guides WHERE id = ?', (report_id,))
        r = cursor.fetchone()
        conn.close()
        if r:
            context = f"The user is asking about their furniture: {r['furniture_name']} ({r['furniture_type']}), material: {r['material']}, brand: {r['brand']}, age: {r['age']}, condition: {r['condition']}, problem: {r['problem_description']}. "

    prompt = f"""
    You are AURA AI, an elite furniture care chatbot.
    {context}
    The user asks: "{message}"
    
    Provide a professional, friendly, and expert answer. Keep it concise, helpful, and focused on furniture care, cleaning, or restoration.
    """

    try:
        gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
        headers = { 'Content-Type': 'application/json' }
        payload = {
            "contents": [{
                "parts": [{
                    "text": prompt
                }]
            }]
        }
        
        response = requests.post(gemini_url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        resp_json = response.json()
        raw_text = resp_json['candidates'][0]['content']['parts'][0]['text'].strip()
        return jsonify({ 'response': raw_text })
    except Exception as e:
        print(f"Chatbot Gemini Error: {str(e)}")
        return jsonify({ 'error': f"Gemini API Error: {str(e)}" }), 502

# Serve static frontend files
@app.route('/')
def serve_index():
    return send_from_directory('public', 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    # Security check to prevent traversing outside public directory
    if '..' in filename or filename.startswith('/'):
        return jsonify({ 'error': 'Access denied.' }), 403
    return send_from_directory('public', filename)

if __name__ == '__main__':
    app.run(port=8000, debug=True)
