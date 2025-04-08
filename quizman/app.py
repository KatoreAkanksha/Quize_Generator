from flask import Flask, redirect, url_for
from flask_cors import CORS
from dotenv import load_dotenv
import os
import urllib.parse
from flask import render_template
from extensions import db, login_manager
from datetime import datetime
from models import Teacher, Student

# Load environment variables
load_dotenv()

@login_manager.user_loader
def load_user(user_id):
    # Try to load teacher first
    teacher = Teacher.query.get(int(user_id))
    if teacher:
        return teacher
    # If not a teacher, try to load student
    return Student.query.get(int(user_id))

def create_app():
    app = Flask(__name__, static_folder='static')
    CORS(app)

    # Configure SQLite database
    app.config['SECRET_KEY'] = os.urandom(24)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///quiz.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login_student'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'

    # Register blueprints
    from blueprints.auth import auth_bp
    from blueprints.teacher import teacher_bp
    from blueprints.student import student_bp
    from blueprints.quiz import quiz_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(teacher_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(quiz_bp)

    # Create database tables
    with app.app_context():
        db.create_all()

    @app.route('/')
    def home():
        # Render the new landing page instead of redirecting
        return render_template('landing_page.html')

    @app.context_processor
    def inject_now():
        return {'now': datetime.utcnow()}

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)