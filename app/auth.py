
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required
from .models import User, Role
from . import db

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role','EMPLOYEE')
        if not name or not email or not password:
            flash('All fields are required','danger')
            return render_template('register.html')
        if User.query.filter_by(email=email).first():
            flash('Email already exists','warning')
            return render_template('register.html')
        u = User(name=name, email=email, role=role)
        u.set_password(password)
        db.session.add(u)
        db.session.commit()
        flash('Registered successfully. Please login','success')
        return redirect(url_for('auth.login'))
    return render_template('register.html')

@auth_bp.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user)
            flash('Welcome back!','success')
            if user.role == Role.ADMIN:
                return redirect(url_for('admin.dashboard'))
            return redirect(url_for('attendance.my_attendance'))
        flash('Invalid credentials','danger')
    return render_template('login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out','info')
    return redirect(url_for('auth.login'))
