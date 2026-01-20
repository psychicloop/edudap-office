from flask import Blueprint, render_template, redirect, url_for, request, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user
from .models import User, db

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    # If user is already logged in, send them to dashboard
    if current_user.is_authenticated:
        return redirect(url_for('admin.dashboard'))

    if request.method == 'POST':
        u = request.form.get('username')
        p = request.form.get('password')
        user = User.query.filter_by(username=u).first()
        if user and check_password_hash(user.password_hash, p):
            login_user(user)
            return redirect(url_for('admin.dashboard'))
        flash('Invalid username or password.', 'danger')
    return render_template('login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    # Note: We allow logged-in users to access this if they want to create other accounts,
    # or you can uncomment the next two lines to block logged-in users from registering.
    # if current_user.is_authenticated:
    #     return redirect(url_for('admin.dashboard'))

    if request.method == 'POST':
        u = request.form.get('username')
        e = request.form.get('email')
        p = request.form.get('password')
        r = request.form.get('role', 'Employee')

        if User.query.filter_by(username=u).first():
            flash('This Name is already taken. Choose another.', 'warning')
            return redirect(url_for('auth.register'))
            
        if User.query.filter_by(email=e).first():
            flash('This Email is already in use. Please use a different one.', 'warning')
            return redirect(url_for('auth.register'))

        # Create the new user
        new_user = User(username=u, email=e, role=r, password_hash=generate_password_hash(p))
        db.session.add(new_user)
        db.session.commit()
        
        # STRICT FLOW: Register -> Login Page (Do not auto-login)
        flash('Account created successfully! Please log in.', 'success')
        return redirect(url_for('auth.login'))
        
    return render_template('register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/magic-reset')
def magic_reset():
    db.drop_all()
    db.create_all()
    return "DATABASE CLEANED. Go to /auth/register and register your Admin account now."
