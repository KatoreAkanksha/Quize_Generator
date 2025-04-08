from extensions import db
from flask_login import UserMixin
from datetime import datetime

# Association table for quiz-student assignments
quiz_students = db.Table('quiz_students',
    db.Column('quiz_id', db.Integer, db.ForeignKey('quizzes.quiz_id'), primary_key=True),
    db.Column('student_id', db.Integer, db.ForeignKey('students.student_id'), primary_key=True)
)

class Teacher(UserMixin, db.Model):
    __tablename__ = 'teachers'
    teacher_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    quizzes = db.relationship('Quiz', backref='teacher', lazy=True)

    def get_id(self):
        return str(self.teacher_id)

class Student(UserMixin, db.Model):
    __tablename__ = 'students'
    student_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    attempts = db.relationship('Attempt', backref='student', lazy=True)
    assigned_quizzes = db.relationship('Quiz', secondary=quiz_students, lazy='subquery',
        backref=db.backref('assigned_students', lazy=True))

    def get_id(self):
        return str(self.student_id)

class Quiz(db.Model):
    __tablename__ = 'quizzes'
    quiz_id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.teacher_id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    difficulty = db.Column(db.String(20), nullable=False)
    time_limit = db.Column(db.Integer, nullable=False)  # in minutes
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    questions = db.relationship('Question', backref='quiz', lazy=True)
    attempts = db.relationship('Attempt', backref='quiz', lazy=True)

class Question(db.Model):
    __tablename__ = 'questions'
    question_id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quizzes.quiz_id'), nullable=False)
    question_text = db.Column(db.Text, nullable=False)
    option_a = db.Column(db.String(200), nullable=False)
    option_b = db.Column(db.String(200), nullable=False)
    option_c = db.Column(db.String(200), nullable=False)
    option_d = db.Column(db.String(200), nullable=False)
    correct_option = db.Column(db.String(1), nullable=False)
    answers = db.relationship('Answer', backref='question', lazy=True)

class Attempt(db.Model):
    __tablename__ = 'attempts'
    attempt_id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.student_id'), nullable=False)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quizzes.quiz_id'), nullable=False)
    score = db.Column(db.Float, nullable=False)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    answers = db.relationship('Answer', backref='attempt', lazy=True)

class Answer(db.Model):
    __tablename__ = 'answers'
    answer_id = db.Column(db.Integer, primary_key=True)
    attempt_id = db.Column(db.Integer, db.ForeignKey('attempts.attempt_id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.question_id'), nullable=False)
    selected_option = db.Column(db.String(1), nullable=False)
    is_correct = db.Column(db.Boolean, nullable=False)