from app import app, db
import os

with app.app_context():
    db.create_all()
    print("✅ Database tables created successfully!")
    
    # Create upload directories
    os.makedirs('static/uploads/pets', exist_ok=True)
    os.makedirs('static/uploads/documents', exist_ok=True)
    print("✅ Upload directories created!")
