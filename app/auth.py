from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from .models import User, db

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('admin.dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role')

        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email already exists.', 'danger')
            return redirect(url_for('auth.register'))
        
        new_user = User(
            username=username, 
            email=email, 
            password_hash=generate_password_hash(password, method='pbkdf2:sha256'),
            role=role if role else 'Employee'
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        # --- SURGICAL FIX: Clear session to prevent identity bleed ---
        session.clear()
        login_user(new_user)
        session.modified = True
        
        flash('Account created successfully! Welcome.', 'success')
        return redirect(url_for('admin.dashboard'))

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
            # --- SURGICAL FIX: Clear session to prevent fixation ---
            session.clear()
            login_user(user, remember=True)
            session.modified = True
            
            return redirect(url_for('admin.dashboard'))
        else:
            flash('Login failed. Check email and password.', 'danger')
            
    return render_template('login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    # --- SURGICAL FIX: Ensure session is wiped clean ---
    session.clear()
    session.modified = True
    
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/magic-reset')
def magic_reset():
    db.drop_all()
    db.create_all()
    return "Database has been reset."
