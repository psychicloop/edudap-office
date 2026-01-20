from flask import Blueprint, render_template, redirect, url_for, request, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required
from .models import User, Role
from . import db

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Check if user exists
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('admin.dashboard'))
        else:
            flash('Login Failed. Please check your email and password.', 'danger')
            
    return render_template('login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # 1. Get data from form
        email = request.form.get('email')
        # We look for 'username' OR 'name' to be safe
        username = request.form.get('username') or request.form.get('name')
        password = request.form.get('password')
        role = request.form.get('role')

        # 2. Check if user exists
        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email already exists.', 'warning')
            return redirect(url_for('auth.register'))

        # 3. Create new user (FIXED: Using 'username', NOT 'name')
        new_user = User(
            email=email,
            username=username, 
            password=generate_password_hash(password, method='pbkdf2:sha256'),
            role=role if role else Role.USER
        )
        
        # 4. Save to DB
        db.session.add(new_user)
        db.session.commit()
        
        flash('Account created! You can now login.', 'success')
        return redirect(url_for('auth.login'))
        
    return render_template('register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

# --- MAGIC RESET BUTTON ---
# Use this if you get a "Database Error"
@auth_bp.route('/magic-reset')
def magic_reset():
    from . import db
    try:
        db.drop_all()
        db.create_all()
        return """
        <div style="text-align:center; padding:50px; font-family:sans-serif;">
            <h1 style="color:green;">✅ Database Reset Successful!</h1>
            <p>The database matches the code now.</p>
            <a href="/auth/register" style="background:#0F4C81; color:white; padding:10px 20px; text-decoration:none; border-radius:5px;">Go to Register</a>
        </div>
        """
    except Exception as e:
        return f"<h1>Error:</h1> <p>{str(e)}</p>"
