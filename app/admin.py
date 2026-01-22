from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from functools import wraps
from sqlalchemy import or_
from .models import User, Quotation, ProductData, db

admin_bp = Blueprint('admin', __name__)

def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated: return redirect(url_for('auth.login'))
        if getattr(current_user, 'role', None) != 'Admin':
            flash('Admin access required.', 'danger')
            return redirect(url_for('admin.dashboard'))
        return fn(*args, **kwargs)
    return wrapper

@admin_bp.route('/dashboard', methods=['GET'])
@login_required
def dashboard():
    search_query = request.args.get('q', '').strip()
    
    # GATHER LIVE STATS
    try:
        total_files = Quotation.query.count()
        vendor_count = db.session.query(ProductData.make).distinct().count()
    except:
        total_files = 0
        vendor_count = 0

    results = {'files': [], 'product_matches': []}

    # PERFORM SEARCH
    if search_query:
        # Search Files
        results['files'] = Quotation.query.filter(Quotation.filename.ilike(f'%{search_query}%')).limit(5).all()
        # Search Items
        products = ProductData.query.filter(
            or_(ProductData.cat_no.ilike(f'%{search_query}%'), 
                ProductData.item_description.ilike(f'%{search_query}%'))
        ).limit(20).all()
        
        for p in products:
            results['product_matches'].append({
                'item_name': p.item_description, 'make': p.make, 'cat_no': p.cat_no, 'rate': p.rate
            })

    # Get Recent Files
    try:
        recent_files = Quotation.query.order_by(Quotation.upload_date.desc()).limit(5).all()
    except:
        recent_files = []

    stats = { "total_files": total_files, "vendor_count": vendor_count, "results": results, "search_query": search_query, "files": recent_files }
    return render_template('dashboard.html', **stats)

# --- API FOR LIVE SEARCH ---
@admin_bp.route('/api/search', methods=['GET'])
@login_required
def api_search():
    q = request.args.get('q', '').strip()
    if len(q) < 2: return jsonify({'results': []})
    
    products = ProductData.query.filter(ProductData.item_description.ilike(f'%{q}%')).limit(5).all()
    data = [{'item': p.item_description, 'make': p.make, 'rate': p.rate} for p in products]
    return jsonify({'results': data})

# --- OTHER ROUTES ---
@admin_bp.route('/upload', methods=['GET', 'POST'])
@login_required
def upload_file():
    # POST logic disabled for safety until we confirm DB is stable
    return render_template('upload.html')

@admin_bp.route('/users')
@login_required
def manage_users():
    users = User.query.all()
    return render_template('manage_users.html', users=users)
