from flask import Flask, request, jsonify, render_template
import google.generativeai as genai
import json
import re
import os

app = Flask(__name__)

# ✅ Set your Gemini API key
genai.configure(api_key="AIzaSyDPJoXppCcIzrg5uUTqMfZZIW5oIpfs3aI")  # 🔑 Replace with your Gemini API key

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    topic = request.form.get('topic', '').strip()
    if not topic:
        return jsonify([])

    # Prompt to Gemini model
    prompt = f"""
    Generate exactly 5 multiple-choice quiz questions about "{topic}".
    Format the result as a JSON array like this:
    [
      {{
        "question": "Your question?",
        "options": ["Option A", "Option B", "Option C", "Option D"],
        "answer": "Correct Option"
      }},
      ...
    ]
    Only return valid JSON. Do not include any explanation or extra text.
    """

    try:
        model = genai.GenerativeModel(model_name="models/gemini-pro")  # ✅ Correct model name and path
        response = model.generate_content(prompt)
        response_text = response.text.strip()

        print("\n🔍 Gemini raw response:\n", response_text)

        # Extract valid JSON from Gemini response
        try:
            questions = json.loads(response_text)
        except json.JSONDecodeError:
            match = re.search(r'\[\s*{.*?}\s*]', response_text, re.DOTALL)
            questions = json.loads(match.group()) if match else []

        return jsonify(questions)

    except Exception as e:
        print("❌ Error from Gemini:", e)
        return jsonify([])

if __name__ == '__main__':
    app.run(debug=True)
