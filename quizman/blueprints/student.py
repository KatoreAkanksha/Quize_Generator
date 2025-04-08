from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime
from models import Quiz, Question, Attempt, Answer, Student
from extensions import db

student_bp = Blueprint('student', __name__)

@student_bp.route('/student/dashboard')
@login_required
def dashboard():
    if not isinstance(current_user, Student):
        return redirect(url_for('auth.login_student'))
    
    # Get assigned quizzes and student's attempts
    quizzes = current_user.assigned_quizzes
    attempts = Attempt.query.filter_by(student_id=current_user.student_id).all()
    attempted_quiz_ids = [attempt.quiz_id for attempt in attempts]
    
    return render_template('student/dashboard.html',
                          quizzes=quizzes,
                          attempted_quiz_ids=attempted_quiz_ids)

@student_bp.route('/student/quiz/<int:quiz_id>')
@login_required
def view_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    
    # Check if student has already attempted this quiz
    attempt = Attempt.query.filter_by(
        student_id=current_user.student_id,
        quiz_id=quiz_id
    ).first()
    
    if attempt:
        flash('You have already attempted this quiz', 'info')
        return redirect(url_for('student.view_result', attempt_id=attempt.attempt_id))
    
    return render_template('student/quiz_info.html', quiz=quiz)

@student_bp.route('/student/quiz/<int:quiz_id>/attempt', methods=['GET', 'POST'])
@login_required
def attempt_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    questions = Question.query.filter_by(quiz_id=quiz_id).all()
    
    if request.method == 'POST':
        # Create new attempt
        attempt = Attempt(
            student_id=current_user.student_id,
            quiz_id=quiz_id,
            score=0,
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow()
        )
        db.session.add(attempt)
        db.session.commit()
        
        # Process answers
        correct_count = 0
        total_questions = len(questions)
        
        for question in questions:
            selected_option = request.form.get(f'question_{question.question_id}')
            is_correct = selected_option == question.correct_option
            
            if is_correct:
                correct_count += 1
            
            answer = Answer(
                attempt_id=attempt.attempt_id,
                question_id=question.question_id,
                selected_option=selected_option,
                is_correct=is_correct
            )
            db.session.add(answer)
        
        # Calculate and update score
        attempt.score = (correct_count / total_questions) * 100
        db.session.commit()
        
        return redirect(url_for('student.view_result', attempt_id=attempt.attempt_id))
    
    return render_template('student/attempt_quiz.html', quiz=quiz, questions=questions)

@student_bp.route('/student/result/<int:attempt_id>')
@login_required
def view_result(attempt_id):
    attempt = Attempt.query.get_or_404(attempt_id)
    
    if attempt.student_id != current_user.student_id:
        flash('Unauthorized access', 'error')
        return redirect(url_for('student.dashboard'))
    
    quiz = Quiz.query.get(attempt.quiz_id)
    answers = Answer.query.filter_by(attempt_id=attempt_id).all()
    
    return render_template('student/result.html',
                          attempt=attempt,
                          quiz=quiz,
                          answers=answers)

@student_bp.route('/student/results')
@login_required
def view_all_results():
    attempts = Attempt.query.filter_by(student_id=current_user.student_id).all()
    return render_template('student/all_results.html', attempts=attempts)