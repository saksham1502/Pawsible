from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Secret key for session management
app.config['SECRET_KEY'] = 'your-secret-key-here-change-this-in-production'

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Upload configuration for pets
UPLOAD_FOLDER = 'static/uploads/pets'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Upload configuration for documents
DOCUMENT_FOLDER = 'static/uploads/documents'
ALLOWED_DOCUMENT_EXTENSIONS = {'pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png', 'txt'}
app.config['DOCUMENT_FOLDER'] = DOCUMENT_FOLDER

db = SQLAlchemy(app)

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    pets = db.relationship('Pet', backref='owner', lazy=True, cascade='all, delete-orphan')

class Pet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    species = db.Column(db.String(50), nullable=False)
    breed = db.Column(db.String(100))
    age = db.Column(db.Integer)
    photo = db.Column(db.String(200))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    documents = db.relationship('Document', backref='pet', lazy=True, cascade='all, delete-orphan')

class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    filename = db.Column(db.String(200), nullable=False)
    doc_type = db.Column(db.String(50))
    pet_id = db.Column(db.Integer, db.ForeignKey('pet.id'), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

class Schedule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    event_type = db.Column(db.String(50))
    date = db.Column(db.DateTime, nullable=False)
    notes = db.Column(db.Text)
    pet_id = db.Column(db.Integer, db.ForeignKey('pet.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class UserSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True)
    email_notifications = db.Column(db.Boolean, default=True)
    vaccination_reminders = db.Column(db.Boolean, default=True)
    upload_confirmations = db.Column(db.Boolean, default=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Integer)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)

def allowed_file(filename, allowed_extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

def generate_unique_filename(filename):
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    name, ext = os.path.splitext(secure_filename(filename))
    return f"{name}_{timestamp}{ext}"

# Authentication API routes
@app.route('/api/signup', methods=['POST'])
def signup():
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400
        
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return jsonify({'error': 'Email already registered'}), 400
        
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        
        return jsonify({
            'message': 'User created successfully',
            'email': email
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/login', methods=['POST'])
def api_login():
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400
        
        user = User.query.filter_by(email=email).first()
        
        if not user or not check_password_hash(user.password, password):
            return jsonify({'error': 'Invalid email or password'}), 401
        
        session['user_id'] = user.id
        session['email'] = user.email
        
        return jsonify({
            'message': 'Login successful',
            'email': user.email
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/logout', methods=['POST'])
def api_logout():
    session.clear()
    return jsonify({'message': 'Logged out successfully'}), 200

@app.route('/api/check-auth', methods=['GET'])
def check_auth():
    if 'user_id' in session:
        return jsonify({'authenticated': True, 'email': session.get('email')}), 200
    return jsonify({'authenticated': False}), 200

# Pet API routes
@app.route('/api/pets', methods=['GET'])
def get_pets():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    pets = Pet.query.filter_by(user_id=session['user_id']).all()
    pets_data = [{
        'id': pet.id,
        'name': pet.name,
        'species': pet.species,
        'breed': pet.breed,
        'age': pet.age,
        'photo': pet.photo
    } for pet in pets]
    
    return jsonify(pets_data), 200

@app.route('/api/pets', methods=['POST'])
def add_pet():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        name = request.form.get('name')
        species = request.form.get('species')
        breed = request.form.get('breed')
        age = request.form.get('age')
        
        if not name or not species:
            return jsonify({'error': 'Name and species are required'}), 400
        
        photo_filename = None
        if 'photo' in request.files:
            photo = request.files['photo']
            if photo and photo.filename and allowed_file(photo.filename, ALLOWED_EXTENSIONS):
                photo_filename = generate_unique_filename(photo.filename)
                os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                photo.save(os.path.join(app.config['UPLOAD_FOLDER'], photo_filename))
        
        new_pet = Pet(
            name=name,
            species=species,
            breed=breed,
            age=int(age) if age else None,
            photo=photo_filename,
            user_id=session['user_id']
        )
        db.session.add(new_pet)
        db.session.commit()
        
        return jsonify({
            'message': 'Pet added successfully',
            'pet': {
                'id': new_pet.id,
                'name': new_pet.name,
                'species': new_pet.species,
                'breed': new_pet.breed,
                'age': new_pet.age,
                'photo': new_pet.photo
            }
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/pets/<int:pet_id>', methods=['DELETE'])
def delete_pet(pet_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    pet = Pet.query.filter_by(id=pet_id, user_id=session['user_id']).first()
    if not pet:
        return jsonify({'error': 'Pet not found'}), 404
    
    # Delete pet photo
    if pet.photo:
        photo_path = os.path.join(app.config['UPLOAD_FOLDER'], pet.photo)
        if os.path.exists(photo_path):
            os.remove(photo_path)
    
    # Delete all documents
    for doc in pet.documents:
        doc_path = os.path.join(app.config['DOCUMENT_FOLDER'], doc.filename)
        if os.path.exists(doc_path):
            os.remove(doc_path)
    
    db.session.delete(pet)
    db.session.commit()
    
    return jsonify({'message': 'Pet deleted successfully'}), 200

# Document API routes
@app.route('/api/pets/<int:pet_id>/documents', methods=['GET'])
def get_documents(pet_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    pet = Pet.query.filter_by(id=pet_id, user_id=session['user_id']).first()
    if not pet:
        return jsonify({'error': 'Pet not found'}), 404
    
    documents = Document.query.filter_by(pet_id=pet_id).all()
    docs_data = [{
        'id': doc.id,
        'name': doc.name,
        'filename': doc.filename,
        'doc_type': doc.doc_type,
        'uploaded_at': doc.uploaded_at.strftime('%Y-%m-%d %H:%M')
    } for doc in documents]
    
    return jsonify(docs_data), 200

@app.route('/api/pets/<int:pet_id>/documents', methods=['POST'])
def upload_document(pet_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    pet = Pet.query.filter_by(id=pet_id, user_id=session['user_id']).first()
    if not pet:
        return jsonify({'error': 'Pet not found'}), 404
    
    try:
        if 'document' not in request.files:
            return jsonify({'error': 'No document provided'}), 400
        
        document = request.files['document']
        doc_name = request.form.get('name')
        doc_type = request.form.get('type')
        
        if not document or not document.filename:
            return jsonify({'error': 'No document selected'}), 400
        
        if not allowed_file(document.filename, ALLOWED_DOCUMENT_EXTENSIONS):
            return jsonify({'error': 'Invalid file type'}), 400
        
        filename = generate_unique_filename(document.filename)
        os.makedirs(app.config['DOCUMENT_FOLDER'], exist_ok=True)
        document.save(os.path.join(app.config['DOCUMENT_FOLDER'], filename))
        
        new_doc = Document(
            name=doc_name or document.filename,
            filename=filename,
            doc_type=doc_type,
            pet_id=pet_id
        )
        db.session.add(new_doc)
        db.session.commit()
        
        return jsonify({
            'message': 'Document uploaded successfully',
            'document': {
                'id': new_doc.id,
                'name': new_doc.name,
                'filename': new_doc.filename,
                'doc_type': new_doc.doc_type
            }
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/documents/<int:doc_id>', methods=['DELETE'])
def delete_document(doc_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    document = Document.query.join(Pet).filter(
        Document.id == doc_id,
        Pet.user_id == session['user_id']
    ).first()
    
    if not document:
        return jsonify({'error': 'Document not found'}), 404
    
    doc_path = os.path.join(app.config['DOCUMENT_FOLDER'], document.filename)
    if os.path.exists(doc_path):
        os.remove(doc_path)
    
    db.session.delete(document)
    db.session.commit()
    
    return jsonify({'message': 'Document deleted successfully'}), 200

# Frontend routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    return render_template('dashboard.html')

@app.route('/schedules')
def schedules():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    return render_template('schedules.html')

@app.route('/settings')
def settings():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    return render_template('settings.html')

# Schedule API routes
@app.route('/api/schedules', methods=['GET'])
def get_schedules():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    schedules = Schedule.query.filter_by(user_id=session['user_id']).all()
    schedules_data = [{
        'id': schedule.id,
        'title': schedule.title,
        'event_type': schedule.event_type,
        'date': schedule.date.strftime('%Y-%m-%d %H:%M'),
        'notes': schedule.notes,
        'pet_id': schedule.pet_id
    } for schedule in schedules]
    
    return jsonify(schedules_data), 200

@app.route('/api/schedules', methods=['POST'])
def add_schedule():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        data = request.get_json()
        title = data.get('title')
        event_type = data.get('event_type')
        date_str = data.get('date')
        notes = data.get('notes')
        pet_id = data.get('pet_id')
        
        if not title or not date_str:
            return jsonify({'error': 'Title and date are required'}), 400
        
        schedule_date = datetime.strptime(date_str, '%Y-%m-%dT%H:%M')
        
        new_schedule = Schedule(
            title=title,
            event_type=event_type,
            date=schedule_date,
            notes=notes,
            pet_id=pet_id,
            user_id=session['user_id']
        )
        db.session.add(new_schedule)
        db.session.commit()
        
        return jsonify({
            'message': 'Schedule added successfully',
            'schedule': {
                'id': new_schedule.id,
                'title': new_schedule.title,
                'event_type': new_schedule.event_type,
                'date': new_schedule.date.strftime('%Y-%m-%d %H:%M')
            }
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/schedules/<int:schedule_id>', methods=['DELETE'])
def delete_schedule(schedule_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    schedule = Schedule.query.filter_by(id=schedule_id, user_id=session['user_id']).first()
    if not schedule:
        return jsonify({'error': 'Schedule not found'}), 404
    
    db.session.delete(schedule)
    db.session.commit()
    
    return jsonify({'message': 'Schedule deleted successfully'}), 200

# User Settings API routes
@app.route('/api/settings', methods=['GET'])
def get_settings():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    user = User.query.get(session['user_id'])
    settings = UserSettings.query.filter_by(user_id=session['user_id']).first()
    
    if not settings:
        settings = UserSettings(user_id=session['user_id'])
        db.session.add(settings)
        db.session.commit()
    
    return jsonify({
        'email': user.email,
        'email_notifications': settings.email_notifications,
        'vaccination_reminders': settings.vaccination_reminders,
        'upload_confirmations': settings.upload_confirmations
    }), 200

@app.route('/api/settings/email', methods=['PUT'])
def update_email():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        data = request.get_json()
        new_email = data.get('email')
        
        if not new_email:
            return jsonify({'error': 'Email is required'}), 400
        
        existing_user = User.query.filter_by(email=new_email).first()
        if existing_user and existing_user.id != session['user_id']:
            return jsonify({'error': 'Email already in use'}), 400
        
        user = User.query.get(session['user_id'])
        user.email = new_email
        session['email'] = new_email
        db.session.commit()
        
        return jsonify({'message': 'Email updated successfully'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/settings/password', methods=['PUT'])
def update_password():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        data = request.get_json()
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        
        if not current_password or not new_password:
            return jsonify({'error': 'Both passwords are required'}), 400
        
        user = User.query.get(session['user_id'])
        
        if not check_password_hash(user.password, current_password):
            return jsonify({'error': 'Current password is incorrect'}), 401
        
        user.password = generate_password_hash(new_password, method='pbkdf2:sha256')
        db.session.commit()
        
        return jsonify({'message': 'Password updated successfully'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/settings/notifications', methods=['PUT'])
def update_notifications():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        data = request.get_json()
        settings = UserSettings.query.filter_by(user_id=session['user_id']).first()
        
        if not settings:
            settings = UserSettings(user_id=session['user_id'])
            db.session.add(settings)
        
        settings.email_notifications = data.get('email_notifications', settings.email_notifications)
        settings.vaccination_reminders = data.get('vaccination_reminders', settings.vaccination_reminders)
        settings.upload_confirmations = data.get('upload_confirmations', settings.upload_confirmations)
        
        db.session.commit()
        
        return jsonify({'message': 'Notification preferences updated successfully'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Feedback API routes
@app.route('/api/feedback', methods=['POST'])
def submit_feedback():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        data = request.get_json()
        message = data.get('message')
        rating = data.get('rating')
        
        if not message:
            return jsonify({'error': 'Feedback message is required'}), 400
        
        new_feedback = Feedback(
            user_id=session['user_id'],
            message=message,
            rating=rating
        )
        db.session.add(new_feedback)
        db.session.commit()
        
        return jsonify({'message': 'Feedback submitted successfully'}), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        os.makedirs(DOCUMENT_FOLDER, exist_ok=True)
    app.run(debug=True, host='0.0.0.0', port=8000)
