import os
import pandas as pd
from datetime import datetime, date
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, send_from_directory
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from .models import Quotation, Expense, Attendance, db
from sqlalchemy import or_

admin_bp = Blueprint('admin', __name__)

ALLOWED_EXTENSIONS = {'pdf', 'xlsx', 'xls'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- DASHBOARD ---
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

# --- ATTENDANCE (NEW) ---
@admin_bp.route('/attendance', methods=['GET', 'POST'])
@login_required
def attendance():
    today = date.today()
    record = Attendance.query.filter_by(user_id=current_user.id, date=today).first()

    if request.method == 'POST':
        action = request.form.get('action')
        now = datetime.now()

        if action == 'punch_in':
            if not record:
                new_record = Attendance(date=today, in_time=now, status='Present', user_id=current_user.id)
                db.session.add(new_record)
                db.session.commit()
                flash('Punched In Successfully!', 'success')
            else:
                flash('You are already punched in for today.', 'info')

        elif action == 'punch_out':
            if record and not record.out_time:
                record.out_time = now
                db.session.commit()
                flash('Punched Out Successfully!', 'warning')
            else:
                flash('Cannot punch out (Already out or not punched in).', 'danger')
        
        return redirect(url_for('admin.attendance'))

    # Get history for the bottom table
    history = Attendance.query.filter_by(user_id=current_user.id).order_by(Attendance.date.desc()).limit(10).all()
    
    return render_template('attendance.html', record=record, history=history, today=today)

# --- UPLOAD & FILES ---
@admin_bp.route('/upload', methods=['GET', 'POST'])
@login_required
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files: return redirect(request.url)
        file = request.files['file']
        if file.filename == '' or not allowed_file(file.filename): return redirect(request.url)
            
        filename = secure_filename(file.filename)
        upload_folder = os.path.join(current_app.root_path, 'static', 'uploads')
        os.makedirs(upload_folder, exist_ok=True)
        file.save(os.path.join(upload_folder, filename))
        
        client = request.form.get('client_name')
        details = request.form.get('product_details')
        new_quote = Quotation(filename=filename, client_name=client, product_details=details, user_id=current_user.id)
        db.session.add(new_quote)
        db.session.commit()
        flash('File uploaded successfully', 'success')
        return redirect(url_for('admin.dashboard'))
    return render_template('upload.html')

@admin_bp.route('/download/<int:file_id>')
@login_required
def download_file(file_id):
    quote = Quotation.query.get_or_404(file_id)
    upload_folder = os.path.join(current_app.root_path, 'static', 'uploads')
    try: return send_from_directory(upload_folder, quote.filename, as_attachment=True)
    except FileNotFoundError: return redirect(url_for('admin.dashboard'))

@admin_bp.route('/view_file/<int:file_id>')
@login_required
def view_file(file_id):
    quote = Quotation.query.get_or_404(file_id)
    upload_folder = os.path.join(current_app.root_path, 'static', 'uploads')
    file_path = os.path.join(upload_folder, quote.filename)
    ext = quote.filename.rsplit('.', 1)[1].lower()
    
    if ext in ['xlsx', 'xls']:
        try:
            df = pd.read_excel(file_path)
            return render_template('excel_view.html', filename=quote.filename, columns=df.columns.tolist(), data=df.fillna('').values.tolist())
        except: return redirect(url_for('admin.dashboard'))
    return redirect(url_for('admin.download_file', file_id=file_id))
