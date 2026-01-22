from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, Response
from flask_login import login_required, current_user
from functools import wraps
from sqlalchemy import or_
from .models import User, Quotation, ProductData, db
import csv
from io import StringIO

admin_bp = Blueprint('admin', __name__)

# --- Security Decorator ---
def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated: return redirect(url_for('auth.login'))
        if getattr(current_user, 'role', None) != 'Admin':
            flash('Admin access required.', 'danger')
            return redirect(url_for('admin.dashboard'))
        return fn(*args, **kwargs)
    return wrapper

# --- 1. DASHBOARD ---
@admin_bp.route('/dashboard', methods=['GET'])
@login_required
def dashboard():
    search_query = request.args.get('q', '').strip()
    
    try:
        total_files = Quotation.query.count()
        vendor_count = db.session.query(ProductData.make).distinct().count()
    except:
        total_files = 0
        vendor_count = 0

    results = {'files': [], 'product_matches': []}

    if search_query:
        results['files'] = Quotation.query.filter(Quotation.filename.ilike(f'%{search_query}%')).limit(5).all()
        products = ProductData.query.filter(
            or_(ProductData.cat_no.ilike(f'%{search_query}%'), 
                ProductData.item_description.ilike(f'%{search_query}%'))
        ).limit(20).all()
        for p in products:
            results['product_matches'].append({
                'item_name': p.item_description, 'make': p.make, 'cat_no': p.cat_no, 'rate': p.rate
            })

    try:
        recent_files = Quotation.query.order_by(Quotation.upload_date.desc()).limit(5).all()
    except:
        recent_files = []

    stats = { "total_files": total_files, "vendor_count": vendor_count, "results": results, "search_query": search_query, "files": recent_files }
    return render_template('dashboard.html', **stats)

# --- 2. UPLOAD ---
@admin_bp.route('/upload', methods=['GET', 'POST'], endpoint='upload_file')
@login_required
def upload_file():
    if request.method == 'POST':
        flash('Upload processing is paused for maintenance.', 'warning')
        return redirect(url_for('admin.dashboard'))
    return render_template('upload.html')

# --- 3. USERS ---
@admin_bp.route('/users', methods=['GET'])
@login_required
@admin_required
def manage_users():
    users = User.query.order_by(User.role.asc()).all()
    return render_template('manage_users.html', users=users)

@admin_bp.route('/promote/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def promote_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.role != 'Admin':
        user.role = 'Admin'
        db.session.commit()
        flash(f'Promoted {user.username}.', 'success')
    return redirect(url_for('admin.manage_users'))

@admin_bp.route('/demote/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def demote_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id != current_user.id and user.role == 'Admin':
        user.role = 'Employee'
        db.session.commit()
        flash(f'Demoted {user.username}.', 'warning')
    return redirect(url_for('admin.manage_users'))

# ---
