from flask import Flask, request, jsonify, render_template, redirect, url_for, session
import google.generativeai as genai
import json
import re
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Add this line for session support

# ✅ Gemini API Key
genai.configure(api_key="AIzaSyBvA3DLZVADphQrPM5_ZTkaJqAdVXfG6M4")# Or replace with "your-api-key"

# Temporary in-memory scoreboard
scoreboard = []

@app.route('/')
def home():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    topic = request.form.get('topic', '').strip()
    mode = request.form.get('mode', 'easy').strip()
    if not topic:
        return jsonify([])

    prompt = f"""
    Generate exactly 5 multiple-choice quiz questions about "{topic}".
    Difficulty: {mode}.
    Format as a JSON array:
    [
      {{
        "question": "Sample question?",
        "options": ["A", "B", "C", "D"],
        "answer": "Correct Answer"
      }},
      ...
    ]
    Only return valid JSON without explanations or extra text.
    """

    try:
        model = genai.GenerativeModel(model_name="models/gemini-1.5-pro")
        response = model.generate_content(prompt)
        response_text = response.text.strip()

        try:
            questions = json.loads(response_text)
        except json.JSONDecodeError:
            match = re.search(r'\[\s*{.*?}\s*]', response_text, re.DOTALL)
            questions = json.loads(match.group()) if match else []

        return jsonify(questions)
    except Exception as e:
        print("❌ Error:", e)
        return jsonify([])

@app.route('/submit', methods=['POST'])
def submit():
    data = request.get_json()
    topic = data.get('topic')
    score = data.get('score')
    time_taken = data.get('time_taken')  # in seconds

    # Store the result in the scoreboard
    scoreboard.append({
        'topic': topic,
        'score': score,
        'time_taken': time_taken
    })
    return jsonify({'status': 'success'})

@app.route('/scoreboard')
def get_scoreboard():
    return jsonify(scoreboard)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == 'admin' and password == 'admin':
            session['logged_in'] = True
            return redirect(url_for('home'))  # Redirect to quiz page
        else:
            error = "Invalid username or password"
            return render_template('login.html', error=error)
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
