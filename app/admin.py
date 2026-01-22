from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from functools import wraps
from .models import User, db 

admin_bp = Blueprint('admin', __name__)

# --- Security Decorator ---
def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if getattr(current_user, 'role', None) != 'Admin':
            flash('Admin access required.', 'danger')
            return redirect(url_for('admin.dashboard'))
        return fn(*args, **kwargs)
    return wrapper

# --- Dashboard Route ---
@admin_bp.route('/dashboard', methods=['GET'])
@login_required
def dashboard():
    # Safe Placeholder Data
    stats = {
        "total_files": 0,
        "vendor_count": 0,
        "product_count": 0,
        "search_count_24h": 0,
        "files": [] 
    }
    # Matches your existing file: app/templates/dashboard.html
    return render_template('dashboard.html', **stats)

# --- Upload Route ---
@admin_bp.route('/upload', methods=['GET', 'POST'], endpoint='upload_file')
@login_required
def upload_file():
    if request.method == 'POST':
        flash('Upload feature temporarily disabled.', 'warning')
        return redirect(url_for('admin.dashboard'))
    
    # Matches your existing file: app/templates/upload.html
    return render_template('upload.html')

# --- User Management ---
@admin_bp.route('/users', methods=['GET'])
@login_required
@admin_required
def manage_users():
    users = User.query.order_by(User.role.asc(), User.username.asc()).all()
    # Matches the new file we will create below
    return render_template('manage_users.html', users=users)

@admin_bp.route('/promote/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def promote_user(user_id):
    user = User.query.get_or_404(user_id)
    if getattr(user, 'role', None) == 'Admin':
        flash('User is already an admin.', 'info')
        return redirect(url_for('admin.manage_users'))
    user.role = 'Admin'
    db.session.commit()
