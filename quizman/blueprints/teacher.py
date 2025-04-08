from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app, session
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from models import db, Quiz, Question, Attempt, Answer, Teacher, Student
from services.gemini_service import GeminiService
from collections import defaultdict
import os

teacher_bp = Blueprint('teacher', __name__)

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'docx', 'pptx'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@teacher_bp.route('/teacher/dashboard')
@login_required
def dashboard():
    if not isinstance(current_user, Teacher):
        return redirect(url_for('auth.login_teacher'))
    
    quizzes = Quiz.query.filter_by(teacher_id=current_user.teacher_id).all()
    return render_template('teacher/dashboard.html', quizzes=quizzes)

@teacher_bp.route('/teacher/upload', methods=['GET', 'POST'])
@login_required
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part', 'error')
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            flash('No selected file', 'error')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            upload_folder = os.path.join(current_app.root_path, 'uploads')
            os.makedirs(upload_folder, exist_ok=True)
            file_path = os.path.join(upload_folder, filename)
            file.save(file_path)
            
            # Get difficulty and question count from form
            difficulty = request.form.get('difficulty', 'medium')
            question_count = int(request.form.get('question_count', 5))
            
            # Generate questions using Gemini service
            gemini_service = GeminiService()
            questions = gemini_service.process_file_and_generate_questions(
                file_path, 
                count=question_count,
                difficulty=difficulty
            )
            
            # Store questions in session for quiz creation
            session['generated_questions'] = questions
            os.remove(file_path)  # Clean up uploaded file
            
            return redirect(url_for('teacher.create_quiz'))
    
    return render_template('teacher/upload.html')

@teacher_bp.route('/teacher/create-from-text')
@login_required
def create_from_text():
    if not isinstance(current_user, Teacher):
        return redirect(url_for('auth.login_teacher'))
    
    return render_template('teacher/create_from_text.html')

@teacher_bp.route('/teacher/create-quiz', methods=['GET', 'POST'])
@login_required
def create_quiz():
    if 'generated_questions' not in session:
        return redirect(url_for('teacher.upload_file'))
    
    if request.method == 'POST':
        title = request.form.get('title')
        difficulty = request.form.get('difficulty')
        time_limit = int(request.form.get('time_limit'))
        
        quiz = Quiz(
            teacher_id=current_user.teacher_id,
            title=title,
            difficulty=difficulty,
            time_limit=time_limit
        )
        db.session.add(quiz)
        db.session.commit()
        
        # Add questions to the quiz
        for q_data in session['generated_questions']:
            question = Question(
                quiz_id=quiz.quiz_id,
                question_text=q_data['question_text'],
                option_a=q_data['options']['a'],
                option_b=q_data['options']['b'],
                option_c=q_data['options']['c'],
                option_d=q_data['options']['d'],
                correct_option=q_data['correct_option']
            )
            db.session.add(question)
        
        db.session.commit()
        session.pop('generated_questions', None)
        flash('Quiz created successfully!', 'success')
        return redirect(url_for('teacher.dashboard'))
    
    return render_template('teacher/create_quiz.html', 
                         questions=session['generated_questions'])

@teacher_bp.route('/teacher/quiz/<int:quiz_id>/stats')
@login_required
def quiz_stats(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    if quiz.teacher_id != current_user.teacher_id:
        flash('Unauthorized access', 'error')
        return redirect(url_for('teacher.dashboard'))
    
    # Get all attempts for this quiz
    attempts = Attempt.query.filter_by(quiz_id=quiz_id).all()
    
    # Calculate statistics
    total_attempts = len(attempts)
    avg_score = sum(attempt.score for attempt in attempts) / total_attempts if total_attempts > 0 else 0
    highest_score = max((attempt.score for attempt in attempts), default=0)
    lowest_score = min((attempt.score for attempt in attempts), default=0)
    
    stats = {
        'total_attempts': total_attempts,
        'average_score': avg_score,
        'highest_score': highest_score,
        'lowest_score': lowest_score
    }
    
    # Get all questions for this quiz
    questions = Question.query.filter_by(quiz_id=quiz_id).all()
    
    # Calculate statistics for each question
    question_stats = {}
    for question in questions:
        answers = Answer.query.filter_by(question_id=question.question_id).all()
        correct = sum(1 for answer in answers if answer.is_correct)
        incorrect = len(answers) - correct
        success_rate = (correct / len(answers) * 100) if answers else 0
        
        question_stats[question.question_id] = {
            'correct': correct,
            'incorrect': incorrect,
            'success_rate': success_rate
        }
    
    return render_template('teacher/quiz_stats.html',
                          quiz=quiz,
                          stats=stats,
                          attempts=attempts,
                          questions=questions,
                          question_stats=question_stats)

@teacher_bp.route('/teacher/quiz/<int:quiz_id>')
@login_required
def view_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    if quiz.teacher_id != current_user.teacher_id:
        flash('Unauthorized access', 'error')
        return redirect(url_for('teacher.dashboard'))
    
    attempts = Attempt.query.filter_by(quiz_id=quiz_id).all()
    return render_template('teacher/view_quiz.html', quiz=quiz, attempts=attempts)

@teacher_bp.route('/teacher/results/<int:quiz_id>')
@login_required
def view_results(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    if not isinstance(current_user, Teacher) or quiz.teacher_id != current_user.teacher_id:
        flash('Unauthorized access', 'error')
        return redirect(url_for('teacher.dashboard'))

    attempts = Attempt.query.filter_by(quiz_id=quiz.quiz_id).all()
    return render_template('teacher/results.html', quiz=quiz, attempts=attempts)

@teacher_bp.route('/teacher/assign-quiz/<int:quiz_id>', methods=['GET', 'POST'])
@login_required
def assign_quiz(quiz_id):
    if not isinstance(current_user, Teacher):
        return redirect(url_for('auth.login_teacher'))
    
    quiz = Quiz.query.get_or_404(quiz_id)
    if quiz.teacher_id != current_user.teacher_id:
        flash('Unauthorized access', 'error')
        return redirect(url_for('teacher.dashboard'))
    
    if request.method == 'POST':
        student_ids = request.form.getlist('students')
        # Clear existing assignments
        quiz.assigned_students = []
        # Add new assignments
        for student_id in student_ids:
            student = Student.query.get(student_id)
            if student:
                quiz.assigned_students.append(student)
        db.session.commit()
        flash('Quiz assigned successfully!', 'success')
        return redirect(url_for('teacher.dashboard'))
    
    # Get all students for the assignment form
    students = Student.query.all()
    return render_template('teacher/assign_quiz.html', quiz=quiz, students=students)