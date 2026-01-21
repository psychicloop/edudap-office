from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from functools import wraps
from .models import Quotation, Expense, Attendance, HolidayRequest, Todo, LocationPing, AssignedTask, User, ProductData, db

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Access Denied.', 'danger')
            return redirect(url_for('admin.dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# --- USER MANAGEMENT ---
@admin_bp.route('/users')
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
    if user.is_admin:
        flash('User is already Admin.', 'info')
    else:
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

    # CHECK: Is this the last admin?
    admin_count = User.query.filter_by(role='Admin').count()
    if admin_count <= 1:
        flash('Cannot demote the last remaining Admin!', 'danger')
        return redirect(url_for('admin.manage_users'))

    user.role = 'Employee'
    db.session.commit()
    flash(f'Demoted {user.username} to Employee.', 'warning')
    return redirect(url_for('admin.manage_users'))

# ... (Keep your existing dashboard/upload/search routes here) ...
