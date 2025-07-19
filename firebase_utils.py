import firebase_admin
from firebase_admin import credentials, firestore

# Initialize Firebase only once
if not firebase_admin._apps:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()

def save_quiz(quiz_data):
    """Save a quiz to Firestore."""
    quizzes_ref = db.collection('quizzes')
    quizzes_ref.add(quiz_data)

def get_all_quizzes():
    """Retrieve all quizzes from Firestore."""
    quizzes_ref = db.collection('quizzes')
    docs = quizzes_ref.stream()
    return [{**doc.to_dict(), 'id': doc.id} for doc in docs]

def get_quiz_by_id(quiz_id):
    """Retrieve a single quiz by its Firestore ID."""
    doc = db.collection('quizzes').document(quiz_id).get()
    return doc.to_dict() if doc.exists else None

def save_rating(quiz_id, rating):
    """Save a rating for a quiz in Firestore."""
    quiz_ref = db.collection('quizzes').document(quiz_id)
    quiz_ref.update({'rating': rating})