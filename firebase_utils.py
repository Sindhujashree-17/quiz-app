import firebase_admin
from firebase_admin import credentials, firestore

# Initialize Firebase only once
if not firebase_admin._apps:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()

def save_user(username, password):
    """Save a new user to Firestore."""
    users_ref = db.collection('users')
    users_ref.add({
        'username': username,
        'password': password
    })

def get_user(username):
    """Retrieve a user by username from Firestore."""
    users_ref = db.collection('users')
    query = users_ref.where('username', '==', username).limit(1).stream()
    for doc in query:
        return doc.to_dict()
    return None

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