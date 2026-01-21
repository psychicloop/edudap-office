import os
import pandas as pd
from datetime import datetime, date
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, send_from_directory
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from .models import Quotation, Expense, Attendance, HolidayRequest, Todo, LocationPing, db
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
    user_expenses = Expense.query.filter_by(user_id=current_user.id, status='Pending').all()

    stats = {
        'quote_count': len(user_quotes),
        'expense_total': sum(e.amount for e in user_expenses) if user_expenses else 0,
        'role': current_user.role
    }

    return render_template('dashboard.html', stats=stats, quotes=user_quotes)

# --- ATTENDANCE (UPDATED WITH LOCATION) ---
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
                # CAPTURE LOCATION
                lat = request.form.get('latitude')
                lng = request.form.get('longitude')
                
                new_record = Attendance(date=today, in_time=now, status='Present', user_id=current_user.id)
                db.session.add(new_record)
                
                # Save Ping if location exists
                if lat and lng:
                    new_ping = LocationPing(latitude=float(lat), longitude=float(lng), timestamp=now, user_id=current_user.id)
                    db.session.add(new_ping)
                
                db.session.commit()
                flash('Punched In Successfully (Location Captured).', 'success')
            else:
                flash('Already punched in.', 'info')

        elif action == 'punch_out':
            if record and not record.out_time:
                record.out_time = now
                db.session.commit()
                flash('Punched Out Successfully.', 'warning')
            else:
                flash('Cannot punch out.', 'danger')
        
        return redirect(url_for('admin.attendance'))

    history = Attendance.query.filter_by(user_id=current_user.id).order_by(Attendance.date.desc()).limit(10).all()
    return render_template('attendance.html', record=record, history=history, today=today)

# --- LEAVE ---
@admin_bp.route('/leave', methods=['GET', 'POST'])
@login_required
def leave():
    if request.method == 'POST':
        start = request.form.get('start_date')
        end = request.form.get('end_date')
        reason = request.form.get('reason')
        if start and end and reason:
            start_dt = datetime.strptime(start, '%Y-%m-%d').date()
            end_dt = datetime.strptime(end, '%Y-%m-%d').date()
            new_req = HolidayRequest(start_date=start_dt, end_date=end_dt, reason=reason, status='Pending', user_id=current_user.id)
            db.session.add(new_req)
            db.session.commit()
            flash('Leave request submitted.', 'success')
            return redirect(url_for('admin.leave'))
        else:
            flash('Please fill in all fields.', 'danger')

    history = HolidayRequest.query.filter_by(user_id=current_user.id).order_by(HolidayRequest.start_date.desc()).all()
    return render_template('leave.html', history=history)

# --- EXPENSES ---
@admin_bp.route('/expenses', methods=['GET', 'POST'])
@login_required
def expenses():
    if request.method == 'POST':
        exp_date = request.form.get('date')
        category = request.form.get('category')
        amount = request.form.get('amount')
        desc = request.form.get('description')
        if exp_date and category and amount:
            date_obj = datetime.strptime(exp_date, '%Y-%m-%d').date()
            new_exp = Expense(date=date_obj, category=category, amount=float(amount), description=desc, status='Pending', user_id=current_user.id)
            db.session.add(new_exp)
            db.session.commit()
            flash('Expense added successfully.', 'success')
            return redirect(url_for('admin.expenses'))
            
    history = Expense.query.filter_by(user_id=current_user.id).order_by(Expense.date.desc()).all()
    return render_template('expenses.html', history=history)

# --- TODO LIST ---
@admin_bp.route('/todo', methods=['GET', 'POST'])
@login_required
def todo():
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'add':
            title = request.form.get('title')
            due_str = request.form.get('due_date') 
            priority = request.form.get('priority')
            due_dt = None
            if due_str: due_dt = datetime.strptime(due_str, '%Y-%m-%dT%H:%M')
            
            if title:
                new_task = Todo(title=title, due_date=due_dt, priority=priority, status='Pending', user_id=current_user.id)
                db.session.add(new_task)
                db.session.commit()
                flash('Task added.', 'success')
        
        elif action == 'complete':
            task_id = request.form.get('task_id')
            task = Todo.query.get(task_id)
            if task and task.user_id == current_user.id:
                task.status = 'Completed'
                db.session.commit()
                flash('Task completed!', 'success')
                
        elif action == 'delete':
            task_id = request.form.get('task_id')
            task = Todo.query.get(task_id)
            if task and task.user_id == current_user.id:
                db.session.delete(task)
                db.session.commit()
                flash('Task deleted.', 'info')

        return redirect(url_for('admin.todo'))

    tasks = Todo.query.filter_by(user_id=current_user.id).order_by(Todo.due_date.asc()).all()
    pending_tasks = [t for t in tasks if t.status == 'Pending']
    completed_tasks = [t for t in tasks if t.status == 'Completed']
    return render_template('todo.html', pending_tasks=pending_tasks, completed_tasks=completed_tasks, now=datetime.now())

# --- ADMIN PANEL (NEW COMMAND CENTER) ---
@admin_bp.route('/admin-panel')
@login_required
def admin_panel():
    if current_user.role != 'Admin':
        flash('Access Denied.', 'danger')
        return redirect(url_for('admin.dashboard'))
    
    # 1. Get Pending Approvals
    pending_leaves = HolidayRequest.query.filter_by(status='Pending').all()
    pending_expenses = Expense.query.filter_by(status='Pending').all()
    
    # 2. Get Today's Live Attendance
    today = date.today()
    attendance_records = Attendance.query.filter_by(date=today).all()
    
    # Attach location data manually to records
    live_map_data = []
    for record in attendance_records:
        # Get latest ping for this user today
        ping = LocationPing.query.filter_by(user_id=record.user_id).order_by(LocationPing.timestamp.desc()).first()
        if ping:
            live_map_data.append({
                'username': record.user.username,
                'in_time': record.in_time,
                'lat': ping.latitude,
                'lng': ping.longitude
            })
            
    return render_template('admin_panel.html', leaves=pending_leaves, expenses=pending_expenses, map_data=live_map_data)

# --- APPROVE / REJECT ACTIONS ---
@admin_bp.route('/approve-leave/<int:id>')
@login_required
def approve_leave(id):
    if current_user.role == 'Admin':
        req = HolidayRequest.query.get(id)
        req.status = 'Approved'
        db.session.commit()
        flash('Leave Approved', 'success')
    return redirect(url_for('admin.admin_panel'))

@admin_bp.route('/reject-leave/<int:id>')
@login_required
def reject_leave(id):
    if current_user.role == 'Admin':
        req = HolidayRequest.query.get(id)
        req.status = 'Rejected'
        db.session.commit()
        flash('Leave Rejected', 'danger')
    return redirect(url_for('admin.admin_panel'))

@admin_bp.route('/approve-expense/<int:id>')
@login_required
def approve_expense(id):
    if current_user.role == 'Admin':
        req = Expense.query.get(id)
        req.status = 'Approved'
        db.session.commit()
        flash('Expense Approved', 'success')
    return redirect(url_for('admin.admin_panel'))

@admin_bp.route('/reject-expense/<int:id>')
@login_required
def reject_expense(id):
    if current_user.role == 'Admin':
        req = Expense.query.get(id)
        req.status = 'Rejected'
        db.session.commit()
        flash('Expense Rejected', 'danger')
    return redirect(url_for('admin.admin_panel'))

# --- UPLOAD, DOWNLOAD, VIEW (SAFE HOUSE) ---
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
