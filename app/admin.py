import os
import pandas as pd
from datetime import datetime, date, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, send_from_directory, Response
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from .models import Quotation, Expense, Attendance, HolidayRequest, Todo, LocationPing, AssignedTask, User, ProductData, db
from sqlalchemy import or_, extract

admin_bp = Blueprint('admin', __name__)

ALLOWED_EXTENSIONS = {'pdf', 'xlsx', 'xls', 'jpg', 'jpeg', 'png'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- DASHBOARD (THE SMART SEARCH ENGINE) ---
@admin_bp.route('/dashboard')
@login_required
def dashboard():
    query = request.args.get('q')
    
    # 1. Permission Logic
    if current_user.role == 'Admin':
        file_query = Quotation.query
    else:
        file_query = Quotation.query.filter_by(user_id=current_user.id)

    search_results = {'files': [], 'product_matches': []}
    
    if query:
        search_term = f"%{query}%"
        
        # A. Find Files (Filename or Client Name)
        search_results['files'] = file_query.filter(
            or_(
                Quotation.filename.ilike(search_term),
                Quotation.client_name.ilike(search_term)
            )
        ).order_by(Quotation.uploaded_at.desc()).all()
        
        # B. Find SPECIFIC ITEMS (The "Awesome" Search)
        # It looks inside the ProductData table for Descriptions, Makes, Cat Nos, etc.
        item_query = ProductData.query.join(Quotation).filter(
            or_(
                ProductData.item_name.ilike(search_term),
                ProductData.make.ilike(search_term),
                ProductData.cat_no.ilike(search_term),
                ProductData.reagent_kit.ilike(search_term),
                ProductData.description.ilike(search_term)
            )
        )
        
        # Apply permissions to Item Search too
        if current_user.role != 'Admin':
            item_query = item_query.filter(Quotation.user_id == current_user.id)
            
        search_results['product_matches'] = item_query.limit(50).all() 
    
    else:
        # No search? Just show latest uploads
        search_results['files'] = file_query.order_by(Quotation.uploaded_at.desc()).limit(20).all()
    
    # Stats Calculation
    user_expenses = Expense.query.filter_by(user_id=current_user.id, status='Pending').all()
    stats = {'quote_count': len(search_results['files']), 'expense_total': sum(e.amount for e in user_expenses) if user_expenses else 0, 'role': current_user.role}
    
    return render_template('dashboard.html', results=search_results, stats=stats)

# --- UPLOAD (THE UNIVERSAL "HEADER HUNTER" PARSER) ---
@admin_bp.route('/upload', methods=['GET', 'POST'])
@login_required
def upload_file():
    if request.method == 'POST':
        f = request.files['file']
        if f and allowed_file(f.filename):
            fn = secure_filename(f.filename)
            path = os.path.join(current_app.root_path, 'static', 'uploads')
            os.makedirs(path, exist_ok=True)
            full_path = os.path.join(path, fn)
            f.save(full_path)
            
            # 1. Save File Record
            new_quote = Quotation(
                filename=fn, 
                client_name=request.form.get('client_name'), 
                product_details=request.form.get('product_details'), 
                user_id=current_user.id
            )
            db.session.add(new_quote)
            db.session.commit()
            
            # 2. EXTRACT DATA (Universal Logic)
            if fn.endswith(('xlsx', 'xls')):
                try:
                    # STEP A: Read without header to scan rows
                    df_raw = pd.read_excel(full_path, header=None)
                    
                    header_row_index = 0
                    found_header = False
                    
                    # STEP B: Hunt for the "Real" Header (Scan first 50 rows)
                    # We look for a row that contains words like 'Description', 'Item', 'Rate', 'Cat'
                    for i, row in df_raw.head(50).iterrows():
                        # Convert row to a single lowercase string for easy checking
                        row_str = " ".join([str(val).lower() for val in row.values])
                        
                        # Logic: If row has (Item OR Description) AND (Rate OR Price OR Amount), it's the header!
                        has_item = any(x in row_str for x in ['item', 'description', 'particular', 'product'])
                        has_rate = any(x in row_str for x in ['rate', 'price', 'amount', 'mrp', 'total'])
                        
                        if has_item and has_rate:
                            header_row_index = i
                            found_header = True
                            break
                    
                    # STEP C: Re-read file with the correct header
                    df = pd.read_excel(full_path, header=header_row_index)
                    
                    # Clean Headers: lowercase, strip spaces
                    df.columns = df.columns.astype(str).str.lower().str.strip()
                    
                    # Define Synonyms
                    col_map = {
                        'item_name': ['item', 'description', 'particular', 'product', 'name', 'desc'],
                        'make': ['make', 'brand', 'company', 'manufacturer', 'mfr'],
                        'cat_no': ['cat', 'cat no', 'catalog', 'catalogue', 'code', 'part no', 'ref'],
                        'reagent_kit': ['reagent', 'kit', 'pack', 'size', 'packing'],
                        'rate': ['rate', 'price', 'mrp', 'amount', 'unit price', 'cost']
                    }

                    # Function to find the best matching column
                    def find_col(possible_names):
                        for candidate in possible_names:
                            for actual_col in df.columns:
                                if candidate in actual_col: 
                                    return actual_col
                        return None

                    count = 0
                    for index, row in df.iterrows():
                        i_name = str(row[find_col(col_map['item_name'])]) if find_col(col_map['item_name']) else None
                        i_make = str(row[find_col(col_map['make'])]) if find_col(col_map['make']) else None
                        i_cat = str(row[find_col(col_map['cat_no'])]) if find_col(col_map['cat_no']) else None
                        i_kit = str(row[find_col(col_map['reagent_kit'])]) if find_col(col_map['reagent_kit']) else None
                        i_rate = str(row[find_col(col_map['rate'])]) if find_col(col_map['rate']) else None
                        
                        def clean(val): return val if val and val.lower() != 'nan' and val.lower() != 'none' else None
                        
                        # SAVE ONLY VALID ROWS (Must have Item Name or Cat No)
                        if clean(i_name) or clean(i_cat):
                            db.session.add(ProductData(
                                quotation_id=new_quote.id,
                                item_name=clean(i_name),
                                make=clean(i_make),
                                cat_no=clean(i_cat),
                                reagent_kit=clean(i_kit),
                                rate=clean(i_rate),
                                description=clean(i_name)
                            ))
                            count += 1
                    
                    db.session.commit()
                    if count > 0:
                        flash(f'Success! Found table at Row {header_row_index + 1} and indexed {count} items.', 'success')
                    else:
                        flash('File uploaded, but no data rows found. Check column names.', 'warning')
                    
                except Exception as e:
                    print(f"Excel Parse Error: {e}")
                    flash('File uploaded, but structure was too complex to read automatically.', 'warning')

            return redirect(url_for('admin.dashboard'))
    return render_template('upload.html')

# --- ASSIGN TASKS ---
@admin_bp.route('/assigned', methods=['GET', 'POST'])
@login_required
def assigned():
    if request.method == 'POST' and 'assign_task' in request.form:
        if current_user.role != 'Admin': return redirect(url_for('admin.dashboard'))
        title, desc, emp_id, deadline = request.form.get('title'), request.form.get('description'), request.form.get('employee_id'), request.form.get('deadline')
        if title and emp_id:
            db.session.add(AssignedTask(title=title, description=desc, assigned_to_id=emp_id, assigned_by_id=current_user.id, deadline=datetime.strptime(deadline, '%Y-%m-%dT%H:%M') if deadline else None))
            db.session.commit()
            flash('Task Assigned', 'success')
            return redirect(url_for('admin.assigned'))

    if request.method == 'POST' and 'update_chat' in request.form:
        task = AssignedTask.query.get(request.form.get('task_id'))
        if task:
            msg = request.form.get('message')
            status = request.form.get('status')
            task.chat_history = (task.chat_history or "") + f"[{datetime.now().strftime('%d-%b %H:%M')}] {current_user.username}: {msg}\n"
            if status: task.status = status
            db.session.commit()
            return redirect(url_for('admin.assigned'))

    employees = User.query.filter_by(role='Employee').all() if current_user.role == 'Admin' else []
    tasks = AssignedTask.query.order_by(AssignedTask.created_at.desc()).all() if current_user.role == 'Admin' else AssignedTask.query.filter_by(assigned_to_id=current_user.id).order_by(AssignedTask.created_at.desc()).all()
    return render_template('assigned.html', tasks=tasks, employees=employees)

# --- ADMIN PANEL ---
@admin_bp.route('/admin-panel')
@login_required
def admin_panel():
    if current_user.role != 'Admin': return redirect(url_for('admin.dashboard'))
    pending_leaves = HolidayRequest.query.filter_by(status='Pending').count()
    pending_expenses = Expense.query.filter_by(status='Pending').count()
    active_staff = Attendance.query.filter_by(date=date.today(), out_time=None).count()
    stats = {'leaves': pending_leaves, 'expenses': pending_expenses, 'active_staff': active_staff}
    return render_template('admin_panel.html', stats=stats)

# --- ADMIN ATTENDANCE ---
@admin_bp.route('/admin/attendance-monitor')
@login_required
def admin_attendance():
    if current_user.role != 'Admin': return redirect(url_for('admin.dashboard'))
    active_records = Attendance.query.filter_by(date=date.today(), out_time=None).all()
    live_map_data = []
    for record in active_records:
        ping = LocationPing.query.filter_by(user_id=record.user_id).order_by(LocationPing.timestamp.desc()).first()
        if ping: live_map_data.append({'username': record.user.username, 'in_time': record.in_time, 'lat': ping.latitude, 'lng': ping.longitude})
    
    records = Attendance.query.order_by(Attendance.date.desc()).all()
    attendance_data = []
    for r in records:
        hours = (r.out_time - r.in_time).total_seconds() / 3600 if r.in_time and r.out_time else 0
        attendance_data.append({'user': r.user.username, 'date': r.date, 'in': r.in_time, 'out': r.out_time, 'hours': round(hours, 2)})
    return render_template('admin_attendance.html', map_data=live_map_data, records=attendance_data)

@admin_bp.route('/admin/export-attendance')
@login_required
def export_attendance():
    records = Attendance.query.order_by(Attendance.date.desc()).all()
    data = []
    for r in records:
        hours = (r.out_time - r.in_time).total_seconds() / 3600 if r.in_time and r.out_time else 0
        data.append({'Employee': r.user.username, 'Date': r.date, 'In': r.in_time, 'Out': r.out_time, 'Hours': round(hours, 2)})
    return Response(pd.DataFrame(data).to_csv(index=False), mimetype="text/csv", headers={"Content-disposition": "attachment; filename=attendance_report.csv"})

# --- EXPENSES ---
@admin_bp.route('/admin/expenses-manage')
@login_required
def admin_expenses():
    if current_user.role != 'Admin': return redirect(url_for('admin.dashboard'))
    pending = Expense.query.filter_by(status='Pending').all()
    history = Expense.query.filter(Expense.status != 'Pending').order_by(Expense.date.desc()).all()
    approved = db.session.query(db.func.sum(Expense.amount)).filter(Expense.status=='Approved').scalar() or 0
    pending_sum = db.session.query(db.func.sum(Expense.amount)).filter(Expense.status=='Pending').scalar() or 0
    return render_template('admin_expenses.html', pending=pending, history=history, stats={'approved': approved, 'pending': pending_sum})

@admin_bp.route('/admin/export-expenses')
@login_required
def export_expenses():
    expenses = Expense.query.order_by(Expense.date.desc()).all()
    data = [{'User': e.user.username, 'Date': e.date, 'Amount': e.amount, 'Status': e.status} for e in expenses]
    return Response(pd.DataFrame(data).to_csv(index=False), mimetype="text/csv", headers={"Content-disposition": "attachment; filename=expense_report.csv"})

# --- STANDARD ROUTES ---
@admin_bp.route('/admin/leaves')
@login_required
def admin_leaves():
    pending = HolidayRequest.query.filter_by(status='Pending').all()
    history = HolidayRequest.query.filter(HolidayRequest.status != 'Pending').order_by(HolidayRequest.start_date.desc()).all()
    return render_template('admin_leaves.html', pending=pending, history=history)

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
                db.session.add(Attendance(date=today, in_time=now, status='Present', user_id=current_user.id))
                if lat and lng: db.session.add(LocationPing(latitude=float(lat), longitude=float(lng), timestamp=now, user_id=current_user.id))
                db.session.commit()
                flash('Punched In.', 'success')
        elif action == 'punch_out':
            if record and not record.out_time:
                record.out_time = now
                db.session.commit()
                flash('Punched Out.', 'warning')
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
        if exp_date and amount:
            db.session.add(Expense(date=datetime.strptime(exp_date, '%Y-%m-%d').date(), category=category, amount=float(amount), description=desc, bill_image=filename, status='Pending', user_id=current_user.id))
            db.session.commit()
            flash('Expense Submitted', 'success')
            return redirect(url_for('admin.expenses'))
    history = Expense.query.filter_by(user_id=current_user.id).order_by(Expense.date.desc()).all()
    return render_template('expenses.html', history=history)

@admin_bp.route('/todo', methods=['GET', 'POST'])
@login_required
def todo():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add':
            title, due_str, priority = request.form.get('title'), request.form.get('due_date'), request.form.get('priority')
            db.session.add(Todo(title=title, due_date=datetime.strptime(due_str, '%Y-%m-%dT%H:%M') if due_str else None, priority=priority, user_id=current_user.id))
            db.session.commit()
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

# Approvals & View Files
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
