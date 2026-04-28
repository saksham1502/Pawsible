# 🐾 Pawsible Platform

A comprehensive web-based pet management system that helps pet owners organize and access all their pets' information in one secure place.

## Features

- **User Authentication**: Secure signup/login with password hashing
- **Pet Management**: Create, view, and manage multiple pet profiles
- **Document Upload**: Store medical records, vaccination certificates, and other important documents
- **Responsive Design**: Works seamlessly on desktop and mobile devices
- **Secure Storage**: User-specific file storage with unique filename generation

## Tech Stack

### Backend
- Flask (Python web framework)
- SQLAlchemy ORM
- SQLite database
- Werkzeug (password hashing & file handling)
- Flask-CORS (Cross-Origin Resource Sharing)

### Frontend
- Bootstrap 5.3.3
- Vanilla JavaScript
- Responsive card-based UI

## Installation

1. Clone the repository:
```bash
git clone <your-repo-url>
cd pawsible-platform
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the application:
```bash
python app.py
```

5. Open your browser and navigate to `http://localhost:8000`

## Deployment on Render

1. Push your code to GitHub
2. Create a new Web Service on Render
3. Connect your GitHub repository
4. Render will automatically detect the `render.yaml` configuration
5. Deploy!

## Project Structure

```
pawsible-platform/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── render.yaml           # Render deployment config
├── templates/
│   ├── index.html        # Landing page with auth
│   └── dashboard.html    # Pet management dashboard
└── static/
    └── uploads/
        ├── pets/         # Pet photos
        └── documents/    # Pet documents
```

## Security Features

- Password hashing with pbkdf2:sha256
- Session-based authentication
- CSRF protection
- Secure file upload with validation
- User-specific data isolation

## API Endpoints

### Authentication
- `POST /api/signup` - Create new user account
- `POST /api/login` - User login
- `POST /api/logout` - User logout
- `GET /api/check-auth` - Check authentication status

### Pets
- `GET /api/pets` - Get all user's pets
- `POST /api/pets` - Add new pet
- `DELETE /api/pets/<id>` - Delete pet

### Documents
- `GET /api/pets/<id>/documents` - Get pet's documents
- `POST /api/pets/<id>/documents` - Upload document
- `DELETE /api/documents/<id>` - Delete document

## License

MIT License

## Author

Built with ❤️ for pet lovers everywhere!
