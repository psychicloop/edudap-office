from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.exc import IntegrityError
from .models import User, SiteFlag, db

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('admin.dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email').lower().strip()
        password = request.form.get('password')

        # Basic Check
        if User.query.filter_by(email=email).first():
            flash('Email already exists.', 'danger')
            return redirect(url_for('auth.register'))
        
        role = 'Employee'
        
        # 1. Race-Safe Admin Claim
        try:
            with db.session.begin_nested():
                flag = SiteFlag(key='first_admin_created', value='1')
                db.session.add(flag)
            role = 'Admin'
        except IntegrityError:
            db.session.rollback()
            # Flag exists -> We are Employee

        # 2. Race-Safe User Creation
        try:
            new_user = User(
                username=username, 
                email=email, 
                password_hash=generate_password_hash(password, method='pbkdf2:sha256'),
                role=role
            )
            db.session.add(new_user)
            db.session.commit()
            
            # Auto-Login
            session.clear()
            login_user(new_user)
            session.modified = True
            
            flash(f'Welcome! You have been registered as {role}.', 'success')
            return redirect(url_for('admin.dashboard'))
            
        except IntegrityError:
            db.session.rollback()
            flash('Username or Email already taken.', 'danger')
            return redirect(url_for('auth.register'))

    return render_template('register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('admin.dashboard'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password_hash, password):
            session.clear()
            login_user(user, remember=True)
            session.modified = True
            return redirect(url_for('admin.dashboard'))
        else:
            flash('Login failed.', 'danger')
            
    return render_template('login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    session.clear()
    session.modified = True
    flash('Logged out.', 'info')
    return redirect(url_for('auth.login'))
