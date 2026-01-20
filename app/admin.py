import os
import pandas as pd
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, send_from_directory
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
    sql_query = Quotation.query.filter_by(user_id=current_user.id)

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
        if 'file' not in request.files:
            flash('No file selected', 'danger')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No file selected', 'danger')
            return redirect(request.url)
            
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            
            # --- 1. SAVE FILE PHYSICALLY ---
            upload_folder = os.path.join(current_app.root_path, 'static', 'uploads')
            os.makedirs(upload_folder, exist_ok=True) # Ensure folder exists
            file.save(os.path.join(upload_folder, filename))
            
            # --- 2. SAVE TO DB ---
            client = request.form.get('client_name')
            details = request.form.get('product_details')
            new_quote = Quotation(filename=filename, client_name=client, product_details=details, user_id=current_user.id)
            db.session.add(new_quote)
            db.session.commit()
            
            flash('File uploaded successfully', 'success')
            return redirect(url_for('admin.dashboard'))
        else:
            flash('Invalid file type. Only PDF and Excel allowed.', 'warning')
    return render_template('upload.html')

@admin_bp.route('/download/<int:file_id>')
@login_required
def download_file(file_id):
    quote = Quotation.query.get_or_404(file_id)
    upload_folder = os.path.join(current_app.root_path, 'static', 'uploads')
    try:
        return send_from_directory(upload_folder, quote.filename, as_attachment=True)
    except FileNotFoundError:
        flash("File not found on server.", "danger")
        return redirect(url_for('admin.dashboard'))

@admin_bp.route('/view_file/<int:file_id>')
@login_required
def view_file(file_id):
    quote = Quotation.query.get_or_404(file_id)
    upload_folder = os.path.join(current_app.root_path, 'static', 'uploads')
    file_path = os.path.join(upload_folder, quote.filename)
    
    ext = quote.filename.rsplit('.', 1)[1].lower()
    
    if ext in ['xlsx', 'xls']:
        try:
            # Read actual file
            df = pd.read_excel(file_path)
            # Create a simple list of rows for the template to render raw
            # replacing NaN with empty string
            data = df.fillna('').values.tolist()
            columns = df.columns.tolist()
            return render_template('excel_view.html', filename=quote.filename, columns=columns, data=data)
        except Exception as e:
            flash(f"Error reading file: {str(e)}", "danger")
            return redirect(url_for('admin.dashboard'))
    else:
        # For PDF, we just download for now (browsers handle PDFs differently)
        return redirect(url_for('admin.download_file', file_id=file_id))
