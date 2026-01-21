from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from functools import wraps
from .models import User, db 

admin_bp = Blueprint('admin', __name__)

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

@admin_bp.route('/dashboard', methods=['GET'])
@login_required
def dashboard():
    stats = {
        "total_files": 0,
        "vendor_count": 0,
        "product_count": 0,
        "search_count_24h": 0,
        "files": [] 
    }
    return render_template('dashboard.html', **stats)

@admin_bp.route('/upload', methods=['GET', 'POST'], endpoint='upload_file')
@login_required
def upload_file():
    if request.method == 'POST':
        flash('Upload feature temporarily disabled.', 'warning')
        return redirect(url_for('admin.dashboard'))
    return render_template('admin/upload.html')

@admin_bp.route('/users', methods=['GET'])
@login_required
@admin_required
def manage_users():
    users = User.query.order_by(User.role.asc(), User.username.asc()).all()
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
    flash(f'Promoted {user.username} to Admin.', 'success')
    return redirect(url_for('admin.manage_users'))

@admin_bp.route('/demote/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def demote_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('Cannot demote yourself.', 'warning')
        return redirect(url_for('admin.manage_users'))
    if getattr(user, 'role', None) == 'Admin':
        if User.query.filter_by(role='Admin').count() <= 1:
            flash('Cannot demote the last remaining admin.', 'danger')
            return redirect(url_for('admin.manage_users'))
    user.role = 'Employee'
    db.session.commit()
    flash(f'Demoted {user.username} to Employee.', 'warning')
    return redirect(url_for('admin.manage_users'))
