from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from functools import wraps
from .models import User, ProductData, db 
# Note: Ensure 'ProductData' matches whatever model you are using to store files/products

admin_bp = Blueprint('admin', __name__)

# --- SECURITY DECORATOR ---
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Access Denied.', 'danger')
            return redirect(url_for('admin.dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# --- DASHBOARD (The Main Page) ---
@admin_bp.route('/dashboard')
@login_required
def dashboard():
    search_query = request.args.get('q', '').strip()
    
    # Basic logic: If searching, filter results. If not, show all (limit 20).
    if search_query:
        # Assuming you are searching ProductData. Adjust model name if needed.
        files = ProductData.query.filter(ProductData.filename.contains(search_query)).all()
        total_files = len(files)
    else:
        files = ProductData.query.order_by(ProductData.upload_date.desc()).limit(20).all()
        total_files = ProductData.query.count()

    # CRITICAL: This points to YOUR specific file 'dashboard_admin.html'
    return render_template('dashboard_admin.html', files=files, total_files=total_files)

# --- UPLOAD ROUTE (Placeholder) ---
@admin_bp.route('/upload', methods=['GET', 'POST'])
@login_required
def upload_file():
    # ... your existing upload logic goes here ...
    return render_template('admin/upload.html') # Or whatever your upload template is

# --- USER MANAGEMENT (Admins Only) ---
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

    admin_count = User.query.filter_by(role='Admin').count()
    if admin_count <= 1:
        flash('Cannot demote the last remaining Admin!', 'danger')
        return redirect(url_for('admin.manage_users'))

    user.role = 'Employee'
    db.session.commit()
    flash(f'Demoted {user.username} to Employee.', 'warning')
    return redirect(url_for('admin.manage_users'))
