from flask import Blueprint, render_template, request, flash, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required
from models import Teacher, Student
from extensions import db

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register/teacher', methods=['GET', 'POST'])
def register_teacher():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')

        teacher = Teacher.query.filter_by(email=email).first()
        if teacher:
            flash('Email already exists', 'error')
            return redirect(url_for('auth.register_teacher'))

        new_teacher = Teacher(
            name=name,
            email=email,
            password=generate_password_hash(password)
        )
        db.session.add(new_teacher)
        db.session.commit()

        flash('Registration successful!', 'success')
        return redirect(url_for('auth.login_teacher'))

    return render_template('auth/register_teacher.html')

@auth_bp.route('/register/student', methods=['GET', 'POST'])
def register_student():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')

        student = Student.query.filter_by(email=email).first()
        if student:
            flash('Email already exists', 'error')
            return redirect(url_for('auth.register_student'))

        new_student = Student(
            name=name,
            email=email,
            password=generate_password_hash(password)
        )
        db.session.add(new_student)
        db.session.commit()

        flash('Registration successful!', 'success')
        return redirect(url_for('auth.login_student'))

    return render_template('auth/register_student.html')

@auth_bp.route('/login/teacher', methods=['GET', 'POST'])
def login_teacher():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        teacher = Teacher.query.filter_by(email=email).first()
        if teacher and check_password_hash(teacher.password, password):
            login_user(teacher)
            flash('Successfully logged in as teacher!', 'success')
            return redirect(url_for('teacher.dashboard'))
        
        flash('Invalid email or password', 'error')
    return render_template('auth/login_teacher.html')

@auth_bp.route('/login/student', methods=['GET', 'POST'])
def login_student():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        student = Student.query.filter_by(email=email).first()
        if student and check_password_hash(student.password, password):
            login_user(student)
            flash('Successfully logged in as student!', 'success')
            return redirect(url_for('student.dashboard'))
        
        flash('Invalid email or password', 'error')
    return render_template('auth/login_student.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login_student'))