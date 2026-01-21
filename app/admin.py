import os
import pandas as pd
from datetime import datetime, date, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, send_from_directory, Response
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from .models import Quotation, Expense, Attendance, HolidayRequest, Todo, LocationPing, db
from sqlalchemy import or_, extract

admin_bp = Blueprint('admin', __name__)

ALLOWED_EXTENSIONS = {'pdf', 'xlsx', 'xls', 'jpg', 'jpeg', 'png'}

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
        sql_query = sql_query.filter(or_(Quotation.filename.ilike(search), Quotation.client_name.ilike(search), Quotation.product_details.ilike(search)))
    user_quotes = sql_query.order_by(Quotation.uploaded_at.desc()).all()
    user_expenses = Expense.query.filter_by(user_id=current_user.id, status='Pending').all()
    stats = {'quote_count': len(user_quotes), 'expense_total': sum(e.amount for e in user_expenses) if user_expenses else 0, 'role': current_user.role}
    return render_template('dashboard.html', stats=stats, quotes=user_quotes)

# --- 1. ADMIN PANEL (MAIN HUB) ---
@admin_bp.route('/admin-panel')
@login_required
def admin_panel():
    if current_user.role != 'Admin':
        flash('Access Denied.', 'danger')
        return redirect(url_for('admin.dashboard'))
    
    pending_leaves = HolidayRequest.query.filter_by(status='Pending').count()
    pending_expenses = Expense.query.filter_by(status='Pending').count()
    
    # Active Staff: Punched In BUT NOT Punched Out today
    today = date.today()
    active_staff = Attendance.query.filter_by(date=today, out_time=None).count()
    
    stats = {'leaves': pending_leaves, 'expenses': pending_expenses, 'active_staff': active_staff}
    return render_template('admin_panel.html', stats=stats)

# --- 2. ADMIN: ATTENDANCE & MAP ---
@admin_bp.route('/admin/attendance-monitor')
@login_required
def admin_attendance():
    if current_user.role != 'Admin': return redirect(url_for('admin.dashboard'))
    today = date.today()
    
    # Map Data: Only currently punched-in people
    active_records = Attendance.query.filter_by(date=today, out_time=None).all()
    live_map_data = []
    for record in active_records:
        ping = LocationPing.query.filter_by(user_id=record.user_id).order_by(LocationPing.timestamp.desc()).first()
        if ping:
            live_map_data.append({'username': record.user.username, 'in_time': record.in_time, 'lat': ping.latitude, 'lng': ping.longitude})

    # List Data: All records
    records = Attendance.query.order_by(Attendance.date.desc()).all()
    attendance_data = []
    for r in records:
        hours = 0
        if r.in_time and r.out_time:
            hours = (r.out_time - r.in_time).total_seconds() / 3600
        attendance_data.append({'user': r.user.username, 'date': r.date, 'in': r.in_time, 'out': r.out_time, 'hours': round(hours, 2)})

    return render_template('admin_attendance.html', map_data=live_map_data, records=attendance_data)

@admin_bp.route('/admin/export-attendance')
@login_required
def export_attendance():
    if current_user.role != 'Admin': return redirect(url_for('admin.dashboard'))
    records = Attendance.query.order_by(Attendance.date.desc()).all()
    data = []
    for r in records:
        hours = 0
        if r.in_time and r.out_time: hours = (r.out_time - r.in_time).total_seconds() / 3600
        data.append({'Employee': r.user.username, 'Date': r.date, 'In Time': r.in_time, 'Out Time': r.out_time, 'Total Hours': round(hours, 2)})
    
    df = pd.DataFrame(data)
    return Response(df.to_csv(index=False), mimetype="text/csv", headers={"Content-disposition": "attachment; filename=attendance_report.csv"})

# --- 3. ADMIN: LEAVES ---
@admin_bp.route('/admin/leaves')
@login_required
def admin_leaves():
    if current_user.role != 'Admin': return redirect(url_for('admin.dashboard'))
    pending = HolidayRequest.query.filter_by(status='Pending').all()
    history = HolidayRequest.query.filter(HolidayRequest.status != 'Pending').order_by(HolidayRequest.start_date.desc()).all()
    return render_template('admin_leaves.html', pending=pending, history=history)

# --- 4. ADMIN: EXPENSES ---
@admin_bp.route('/admin/expenses-manage')
@login_required
def admin_expenses():
    if current_user.role != 'Admin': return redirect(url_for('admin.dashboard'))
    pending = Expense.query.filter_by(status='Pending').all()
    history = Expense.query.filter(Expense.status != 'Pending').order_by(Expense.date.desc()).all()
    return render_template('admin_expenses.html', pending=pending, history=history)

# --- EMPLOYEE ROUTES ---
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
                lat, lng = request.form.get('latitude'), request.form.get('longitude')
                new_record = Attendance(date=today, in_time=now, status='Present', user_id=current_user.id)
                db.session.add(new_record)
                if lat and lng: db.session.add(LocationPing(latitude=float(lat), longitude=float(lng), timestamp=now, user_id=current_user.id))
                db.session.commit()
                flash('Punched In Successfully.', 'success')
            else: flash('Already punched in.', 'info')
        elif action == 'punch_out':
            if record and not record.out_time:
                record.out_time = now
                db.session.commit()
                flash('Punched Out Successfully.', 'warning')
            else: flash('Cannot punch out.', 'danger')
        return redirect(url_for('admin.attendance'))
    history = Attendance.query.filter_by(user_id=current_user.id).order_by(Attendance.date.desc()).limit(10).all()
    return render_template('attendance.html', record=record, history=history, today=today)

@admin_bp.route('/expenses', methods=['GET', 'POST'])
@login_required
def expenses():
    if request.method == 'POST':
        exp_date, category, amount, desc = request.form.get('date'), request.form.get('category'), request.form.get('amount'), request.form.get('description')
        filename = None
        if 'bill_image' in request.files:
            file = request.files['bill_image']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                os.makedirs(os.path.join(current_app.root_path, 'static', 'uploads'), exist_ok=True)
                file.save(os.path.join(current_app.root_path, 'static', 'uploads', filename))
        if exp_date and category and amount:
            db.session.add(Expense(date=datetime.strptime(exp_date, '%Y-%m-%d').date(), category=category, amount=float(amount), description=desc, bill_image=filename, status='Pending', user_id=current_user.id))
            db.session.commit()
            flash('Expense added.', 'success')
            return redirect(url_for('admin.expenses'))
    history = Expense.query.filter_by(user_id=current_user.id).order_by(Expense.date.desc()).all()
    return render_template('expenses.html', history=history)

# --- TODO & OTHER ROUTES ---
@admin_bp.route('/todo', methods=['GET', 'POST'])
@login_required
def todo():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add':
            title, due_str, priority = request.form.get('title'), request.form.get('due_date'), request.form.get('priority')
            due_dt = datetime.strptime(due_str, '%Y-%m-%dT%H:%M') if due_str else None
            if title: db.session.add(Todo(title=title, due_date=due_dt, priority=priority, user_id=current_user.id)); db.session.commit()
        elif action == 'complete':
            t = Todo.query.get(request.form.get('task_id'))
            if t: t.status = 'Completed'; db.session.commit()
        elif action == 'delete':
            t = Todo.query.get(request.form.get('task_id'))
            if t: db.session.delete(t); db.session.commit()
        return redirect(url_for('admin.todo'))
    tasks = Todo.query.filter_by(user_id=current_user.id).order_by(Todo.due_date.asc()).all()
    return render_template('todo.html', pending_tasks=[t for t in tasks if t.status=='Pending'], completed_tasks=[t for t in tasks if t.status=='Completed'], now=datetime.now())

@admin_bp.route('/leave', methods=['GET', 'POST'])
@login_required
def leave():
    if request.method == 'POST':
        start, end, reason = request.form.get('start_date'), request.form.get('end_date'), request.form.get('reason')
        if start and end: db.session.add(HolidayRequest(start_date=datetime.strptime(start, '%Y-%m-%d').date(), end_date=datetime.strptime(end, '%Y-%m-%d').date(), reason=reason, user_id=current_user.id)); db.session.commit(); flash('Submitted', 'success')
    history = HolidayRequest.query.filter_by(user_id=current_user.id).order_by(HolidayRequest.start_date.desc()).all()
    return render_template('leave.html', history=history)

# APPROVALS
@admin_bp.route('/approve-leave/<int:id>')
@login_required
def approve_leave(id):
    if current_user.role == 'Admin': r=HolidayRequest.query.get(id); r.status='Approved'; db.session.commit()
    return redirect(url_for('admin.admin_leaves'))

@admin_bp.route('/reject-leave/<int:id>')
@login_required
def reject_leave(id):
    if current_user.role == 'Admin': r=HolidayRequest.query.get(id); r.status='Rejected'; db.session.commit()
    return redirect(url_for('admin.admin_leaves'))

@admin_bp.route('/approve-expense/<int:id>')
@login_required
def approve_expense(id):
    if current_user.role == 'Admin': r=Expense.query.get(id); r.status='Approved'; db.session.commit()
    return redirect(url_for('admin.admin_expenses'))

@admin_bp.route('/reject-expense/<int:id>')
@login_required
def reject_expense(id):
    if current_user.role == 'Admin': r=Expense.query.get(id); r.status='Rejected'; db.session.commit()
    return redirect(url_for('admin.admin_expenses'))

@admin_bp.route('/upload', methods=['GET', 'POST'])
@login_required
def upload_file():
    if request.method == 'POST':
        f = request.files['file']
        if f and allowed_file(f.filename):
            fn = secure_filename(f.filename)
            f.save(os.path.join(current_app.root_path, 'static', 'uploads', fn))
            db.session.add(Quotation(filename=fn, client_name=request.form.get('client_name'), product_details=request.form.get('product_details'), user_id=current_user.id)); db.session.commit()
            return redirect(url_for('admin.dashboard'))
    return render_template('upload.html')

@admin_bp.route('/download/<int:file_id>')
@login_required
def download_file(file_id):
    q = Quotation.query.get_or_404(file_id)
    return send_from_directory(os.path.join(current_app.root_path, 'static', 'uploads'), q.filename, as_attachment=True)

@admin_bp.route('/view_file/<int:file_id>')
@login_required
def view_file(file_id):
    q = Quotation.query.get_or_404(file_id)
    path = os.path.join(current_app.root_path, 'static', 'uploads', q.filename)
    if q.filename.endswith(('xlsx', 'xls')):
        try: return render_template('excel_view.html', filename=q.filename, columns=pd.read_excel(path).columns.tolist(), data=pd.read_excel(path).fillna('').values.tolist())
        except: pass
    return redirect(url_for('admin.download_file', file_id=file_id))
