from flask import Blueprint, jsonify, request, url_for, session
from flask_login import login_required, current_user
from models import db, Quiz, Question, Attempt, Teacher
from datetime import datetime
from services.gemini_service import GeminiService

quiz_bp = Blueprint('quiz', __name__)

@quiz_bp.route('/quiz/generate-from-text', methods=['POST'])
@login_required
def generate_from_text():
    # Check if user is a teacher
    if not isinstance(current_user, Teacher):
        return jsonify({'error': 'Unauthorized access'}), 403
    
    # Get text content and parameters from request
    data = request.json
    text_content = data.get('text_content')
    difficulty = data.get('difficulty', 'medium')
    question_count = data.get('question_count', 5)
    
    if not text_content:
        return jsonify({'error': 'No text content provided'}), 400
    
    # Generate questions using Gemini service
    gemini_service = GeminiService()
    questions = gemini_service.generate_questions_with_gemini(
        text_content,
        count=question_count,
        difficulty=difficulty
    )
    
    # Store questions in session for quiz creation
    session['generated_questions'] = questions
    
    return jsonify({
        'success': True,
        'question_count': len(questions),
        'redirect_url': url_for('teacher.create_quiz')
    })

@quiz_bp.route('/quiz/<int:quiz_id>/share')
@login_required
def share_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    
    # Generate shareable link
    share_link = url_for('quiz.view_shared_quiz', quiz_id=quiz_id, _external=True)
    return jsonify({
        'share_link': share_link,
        'quiz_title': quiz.title
    })

@quiz_bp.route('/quiz/<int:quiz_id>/status')
@login_required
def get_quiz_status(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    total_attempts = Attempt.query.filter_by(quiz_id=quiz_id).count()
    completed_attempts = Attempt.query.filter(
        Attempt.quiz_id == quiz_id,
        Attempt.completed_at.isnot(None)
    ).count()
    
    return jsonify({
        'total_attempts': total_attempts,
        'completed_attempts': completed_attempts,
        'is_active': True
    })

@quiz_bp.route('/quiz/<int:quiz_id>/stats')
@login_required
def get_quiz_stats(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    attempts = Attempt.query.filter_by(quiz_id=quiz_id).all()
    
    total_score = sum(attempt.score for attempt in attempts)
    avg_score = total_score / len(attempts) if attempts else 0
    
    stats = {
        'total_attempts': len(attempts),
        'average_score': round(avg_score, 2),
        'highest_score': max((attempt.score for attempt in attempts), default=0),
        'lowest_score': min((attempt.score for attempt in attempts), default=0)
    }
    
    return jsonify(stats)

@quiz_bp.route('/quiz/<int:quiz_id>/time-remaining')
@login_required
def get_time_remaining(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    attempt = Attempt.query.filter_by(
        quiz_id=quiz_id,
        student_id=current_user.student_id,
        completed_at=None
    ).first()
    
    if not attempt:
        return jsonify({'time_remaining': quiz.time_limit * 60})
    
    elapsed_time = (datetime.utcnow() - attempt.started_at).total_seconds()
    time_remaining = max(0, (quiz.time_limit * 60) - elapsed_time)
    
    return jsonify({'time_remaining': int(time_remaining)})