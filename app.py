from flask import Flask, request, jsonify, render_template, redirect, url_for, session
import google.generativeai as genai
import json
import re
import os
from firebase_utils import save_quiz, get_all_quizzes, get_quiz_by_id, save_rating
from flask_session import Session
from dataclasses import dataclass, field
from typing import List, Dict



app = Flask(__name__)
app.secret_key = '24'  # Add this line for session support

app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

# ✅ Gemini API Key
genai.configure(api_key="AIzaSyBvA3DLZVADphQrPM5_ZTkaJqAdVXfG6M4")
scoreboard = []

@app.route('/')
def root():
    # Redirect to login or dashboard depending on session
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return redirect(url_for('dashboard'))


@app.route('/dashboard')
def dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    query = request.args.get('q', '')
    # quizzes = get_filtered_quizzes(query)  # however you're loading quizzes
    return render_template("dashboard.html")  #, quizzes=quizzes


# @app.route('/quiz')
# def quiz():
#     if not session.get('logged_in'):
#         return redirect(url_for('login'))
#     return render_template('index.html')

# @app.route('/generate', methods=['POST'])
# def generate():
#     topic = request.form.get('topic', '').strip()
#     mode = request.form.get('mode', 'easy').strip()
#     if not topic:
#         return jsonify([])

#     prompt = f"""
#     Generate exactly 5 multiple-choice quiz questions about "{topic}".
#     Difficulty: {mode}.
#     Format as a JSON array:
#     [
#       {{
#         "question": "Sample question?",
#         "options": ["A", "B", "C", "D"],
#         "answer": "Correct Answer"
#       }},
#       ...
#     ]
#     Only return valid JSON without explanations or extra text.
#     """

#     try:
#         model = genai.GenerativeModel(model_name="models/gemini-1.5-pro")
#         response = model.generate_content(prompt)
#         response_text = response.text.strip()

#         try:
#             questions = json.loads(response_text)
#         except json.JSONDecodeError:
#             match = re.search(r'\[\s*{.*?}\s*]', response_text, re.DOTALL)
#             questions = json.loads(match.group()) if match else []

#         # Save the generated quiz to Firestore
#         quiz_data = {
#             'topic': topic,
#             'mode': mode,
#             'questions': questions
#         }
#         save_quiz(quiz_data)

#         return jsonify(questions)
#     except Exception as e:
#         print("❌ Error:", e)
#         return jsonify([])


def generate_quiz_from_ai(topic, mode):
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

    model = genai.GenerativeModel(model_name="models/gemini-1.5-pro")
    response = model.generate_content(prompt)
    response_text = response.text.strip()

    try:
        questions = json.loads(response_text)
    except json.JSONDecodeError:
        match = re.search(r'\[\s*{.*?}\s*]', response_text, re.DOTALL)
        questions = json.loads(match.group()) if match else []

    quiz = QuizSession(
        topic=topic,
        mode=mode,
        questions=[Question(**q) for q in questions]
    )

    # Optional: save to Firebase
    save_quiz({
        'topic': topic,
        'mode': mode,
        'questions': questions
    })

    return quiz


@app.route('/generate_quiz', methods=['POST'])
def generate_quiz():
    topic = request.form.get('topic', '').strip()
    mode = request.form.get('mode', 'easy').strip()
    if not topic:
        return redirect(url_for('dashboard'))

    try:
        quiz = generate_quiz_from_ai(topic, mode)
        session['quiz'] = quizsession_to_dict(quiz)
        return redirect(url_for('start_quiz'))
    except Exception as e:
        print("❌ Error:", e)
        return redirect(url_for('dashboard'))

@app.route('/fetch_quizzes')
def fetch_quizzes():
    quizzes = get_all_quizzes()
    return jsonify(quizzes)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == 'admin' and password == 'admin':
            session['logged_in'] = True
            return redirect(url_for('dashboard'))
        else:
            error = "Invalid username or password"
            return render_template('login.html', error=error)
    # GET request (or fallback)
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/rate_quiz', methods=['POST'])
def rate_quiz():
    data = request.get_json()
    quiz_id = data.get('quiz_id')
    rating = data.get('rating')
    save_rating(quiz_id, rating)
    return jsonify({'status': 'success'})


@dataclass
class Question:
    question: str
    options: List[str]
    answer: str

@dataclass
class QuizSession:
    topic: str
    mode: str
    questions: List[Question]
    current_index: int = 0
    user_answers: Dict[int, str] = field(default_factory=dict)



def quizsession_to_dict(quiz_session: QuizSession):
    return {
        "topic": quiz_session.topic,
        "mode": quiz_session.mode,
        "questions": [q.__dict__ for q in quiz_session.questions],
        "current_index": quiz_session.current_index,
        "user_answers": quiz_session.user_answers
    }

def dict_to_quizsession(data: dict) -> QuizSession:
    questions = [Question(**q) for q in data["questions"]]
    return QuizSession(
        topic=data["topic"],
        mode=data["mode"],
        questions=questions,
        current_index=data["current_index"],
        user_answers=data["user_answers"]
    )


@app.route("/quiz/start", methods=["GET", "POST"])
def quiz_start():
    if request.method == "GET":
        return render_template("quiz/quiz.html", show_form=True, show_questions=False, quiz=None)

    elif request.method == "POST":
        if "quiz_id" in request.form:
            quiz_id = request.form["quiz_id"]
            quiz = get_quiz_by_id(quiz_id)
        else:
            topic = request.form["topic"]
            mode = request.form["mode"]
            quiz = generate_quiz_from_ai(topic, mode)  # ✅ Corrected

        session['quiz'] = quizsession_to_dict(quiz)
        return redirect(url_for('show_question'))



@app.route("/quiz/question")
def show_question():
    quiz_dict = session.get("quiz")
    if not quiz_dict:
        return redirect(url_for("quiz_start"))

    quiz = dict_to_quizsession(quiz_dict)
    index = quiz.current_index
    if index >= len(quiz.questions):
        return redirect(url_for("quiz_start"))

    question = quiz.questions[index]

    return render_template(
        "quiz.html",
        show_form=False,
        show_questions=True,
        quiz=quiz,  # ✅ <--- THIS must be passed
        question=question,
        index=index,
        total=len(quiz.questions)
    )




@app.route('/quiz/answer', methods=['POST'])
def answer():
    quiz = dict_to_quizsession(session['quiz'])

    selected = request.form.get('answer')
    nav = request.form.get('nav')

    quiz.user_answers[quiz.current_index] = selected

    if nav == 'next' and quiz.current_index < len(quiz.questions) - 1:
        quiz.current_index += 1
    elif nav == 'prev' and quiz.current_index > 0:
        quiz.current_index -= 1
    elif nav == 'submit':
        session['quiz'] = quizsession_to_dict(quiz)
        return redirect(url_for('submit_quiz'))

    session['quiz'] = quizsession_to_dict(quiz)
    return redirect(url_for('show_question'))


@app.route('/quiz/view/<quiz_id>')
def view_existing_quiz(quiz_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    quiz_data = get_quiz_by_id(quiz_id)
    if not quiz_data:
        return redirect(url_for('dashboard'))

    quiz = QuizSession(
        topic=quiz_data['topic'],
        mode=quiz_data['mode'],
        questions=[Question(**q) for q in quiz_data['questions']]
    )
    session['quiz'] = quizsession_to_dict(quiz)
    return redirect(url_for('start_quiz'))


@app.route('/quiz/submit')
def submit_quiz():
    quiz = dict_to_quizsession(session['quiz'])
    correct = 0
    for i, q in enumerate(quiz.questions):
        if quiz.user_answers.get(i, '').strip().lower() == q.answer.strip().lower():
            correct += 1

    return render_template('result.html', score=correct, total=len(quiz.questions))



if __name__ == '__main__':
    app.run(debug=True)
