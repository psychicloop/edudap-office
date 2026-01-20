import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from .models import Quotation, Expense, db
from sqlalchemy import or_

admin_bp = Blueprint('admin', __name__)

ALLOWED_EXTENSIONS = {'pdf', 'xlsx', 'xls'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@admin_bp.route('/dashboard')
@login_required
def dashboard():
    query = request.args.get('q')
    
    # Base Query
    sql_query = Quotation.query.filter_by(user_id=current_user.id)

    # Search Logic
    if query:
        search = f"%{query}%"
        sql_query = sql_query.filter(
            or_(
                Quotation.filename.ilike(search),
                Quotation.client_name.ilike(search),
                Quotation.product_details.ilike(search)
            )
        )
    
    user_quotes = sql_query.order_by(Quotation.uploaded_at.desc()).all()
    user_expenses = Expense.query.filter_by(user_id=current_user.id).all()

    stats = {
        'quote_count': len(user_quotes),
        'expense_total': sum(e.amount for e in user_expenses) if user_expenses else 0,
        'role': current_user.role
    }

    return render_template('dashboard.html', stats=stats, quotes=user_quotes)

@admin_bp.route('/upload', methods=['GET', 'POST'])
@login_required
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file selected', 'danger')
            return redirect(request.url)
        
        file = request.files['file']
        
        if file.filename == '':
            flash('No file selected', 'danger')
            return redirect(request.url)
            
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            
            # Extract basic info from form if provided
            client = request.form.get('client_name')
            details = request.form.get('product_details')
            
            # Save logic would go here (saving to disk or cloud)
            # For now, we simulate saving to DB
            
            new_quote = Quotation(
                filename=filename,
                client_name=client,
                product_details=details,
                user_id=current_user.id
            )
            db.session.add(new_quote)
            db.session.commit()
            
            flash('File uploaded successfully', 'success')
            return redirect(url_for('admin.dashboard'))
        else:
            flash('Invalid file type. Only PDF and Excel allowed.', 'warning')
            
    return render_template('upload.html')
