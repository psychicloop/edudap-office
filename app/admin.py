
import os

import pandas as pd

from datetime import datetime, date, timedelta

from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, send_from_directory, Response

from flask_login import login_required, current_user

from werkzeug.utils import secure_filename

from .models import Quotation, Expense, Attendance, HolidayRequest, Todo, LocationPing, AssignedTask, User, ProductData, db

from sqlalchemy import or_



admin_bp = Blueprint('admin', __name__)



ALLOWED_EXTENSIONS = {'pdf', 'xlsx', 'xls', 'jpg', 'jpeg', 'png', 'csv'}



def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS



# --- DASHBOARD (SMART SEARCH) ---
@admin_bp.route('/dashboard')
@login_required
def dashboard():
    query = request.args.get('q')
    
    if current_user.role == 'Admin':
        file_query = Quotation.query
    else:
        file_query = Quotation.query.filter_by(user_id=current_user.id)

    search_results = {'files': [], 'product_matches': []}
    
    if query:
        search_term = f"%{query}%"
        
        # 1. Search Files
        search_results['files'] = file_query.filter(
            or_(
                Quotation.filename.ilike(search_term),
                Quotation.client_name.ilike(search_term)
            )
        ).order_by(Quotation.uploaded_at.desc()).all()
        
        # 2. Search Items
        item_query = ProductData.query.join(Quotation).filter(
            or_(
                ProductData.item_name.ilike(search_term),
                ProductData.make.ilike(search_term),
                ProductData.cat_no.ilike(search_term),
                ProductData.reagent_kit.ilike(search_term),
                ProductData.description.ilike(search_term)
            )
        )
        
        if current_user.role != 'Admin':
            item_query = item_query.filter(Quotation.user_id == current_user.id)
            
        search_results['product_matches'] = item_query.limit(50).all()
    
    else:
        search_results['files'] = file_query.order_by(Quotation.uploaded_at.desc()).limit(20).all()
    
    user_expenses = Expense.query.filter_by(user_id=current_user.id, status='Pending').all()
    stats = {
        'quote_count': len(search_results['files']),
        'expense_total': sum(e.amount for e in user_expenses) if user_expenses else 0,
        'role': current_user.role
    }
    
    return render_template('dashboard.html', results=search_results, stats=stats)


# --- SMART SEARCH API (read-only) ---
@admin_bp.route('/api/search')
@login_required
def api_search():
    """
    Returns live smart-search results for type-ahead (2+ characters).
    Searches across ProductData: item_name, make, cat_no, reagent_kit, description.
    Respects Admin vs non-Admin visibility (non-admin sees own uploads only).
    """
    q = (request.args.get('q') or '').strip()
    if len(q) < 2:
        return {'results': []}

    like = f"%{q}%"
    item_query = ProductData.query.join(Quotation).filter(
        or_(
            ProductData.item_name.ilike(like),
            ProductData.make.ilike(like),
            ProductData.cat_no.ilike(like),
            ProductData.reagent_kit.ilike(like),
            ProductData.description.ilike(like)
        )
    )

    if current_user.role != 'Admin':
        item_query = item_query.filter(Quotation.user_id == current_user.id)

    rows = item_query.limit(50).all()

    def as_dict(p):
        return {
            'item': p.item_name,
            'make': p.make,
            'cat_no': p.cat_no,
            'reagent_kit': p.reagent_kit,
            'rate': p.rate,
            'specs': p.description,
            'quotation_id': p.quotation_id
        }

    return {'results': [as_dict(r) for r in rows]}



# --- UPLOAD (FAIL-SAFE PARSER) ---
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
            
            new_quote = Quotation(
                filename=fn, 
                client_name=request.form.get('client_name'), 
                product_details=request.form.get('product_details'), 
                user_id=current_user.id
            )
            db.session.add(new_quote)
            db.session.commit()
            
            if fn.endswith(('xlsx', 'xls', 'csv')):
                try:
                    # 1. READ FILE
                    if fn.endswith('.csv'): 
                        df_raw = pd.read_csv(full_path, header=None, engine='python', on_bad_lines='skip')
                    else: 
                        df_raw = pd.read_excel(full_path, header=None)
                    
                    header_row = -1
                    
                    # 2. FIND HEADER (Look for Rate + Qty)
                    for i, row in df_raw.head(60).iterrows():
                        row_txt = " ".join([str(v).lower() for v in row.values])
                        if 'rate' in row_txt and ('qty' in row_txt or 'quantity' in row_txt):
                            header_row = i
                            break
                    
                    # Fallback
                    if header_row == -1: header_row = 0

                    # 3. RELOAD DATA
                    if fn.endswith('.csv'): 
                        df = pd.read_csv(full_path, header=header_row, engine='python', on_bad_lines='skip')
                    else: 
                        df = pd.read_excel(full_path, header=header_row)
                    
                    # 4. IDENTIFY COLUMN INDICES (The Robust Part)
                    headers = [str(c).lower().strip() for c in df.columns]
                    
                    def get_idx(keywords, default_idx):
                        for i, h in enumerate(headers):
                            if any(k in h for k in keywords): return i
                        return default_idx # Fallback if name not found

                    # Dynamic Mapping with Defaults
                    idx_item = get_idx(['item', 'desc', 'particular'], 1)  # Default: Col B
                    idx_make = get_idx(['make', 'brand', 'company'], 4)    # Default: Col E
                    idx_cat  = get_idx(['cat', 'code', 'part'], 5)         # Default: Col F
                    idx_unit = get_idx(['unit', 'pack', 'kit'], 2)         # Default: Col C
                    idx_rate = get_idx(['rate', 'price', 'amount'], 6)     # Default: Col G

                    count = 0
                    sample_item = ""

                    # 5. EXTRACT DATA
                    for index, row in df.iterrows():
                        vals = list(row.values)
                        
                        # Safe extraction helper
                        def get_val(idx):
                            if 0 <= idx < len(vals):
                                v = str(vals[idx]).strip()
                                return v if v.lower() not in ['nan', 'none', '', '0'] else None
                            return None

                        item = get_val(idx_item)
                        rate = get_val(idx_rate)
                        
                        # Valid Row Rule: Must have Item Name AND (Rate OR CatNo)
                        if item and (rate or get_val(idx_cat)):
                            if 'total' not in item.lower() and 'terms' not in item.lower():
                                db.session.add(ProductData(
                                    quotation_id=new_quote.id,
                                    item_name=item,
                                    make=get_val(idx_make),
                                    cat_no=get_val(idx_cat),
                                    reagent_kit=get_val(idx_unit),
                                    rate=rate,
                                    description=item
                                ))
                                count += 1
                                if count == 1: sample_item = item 
                    
                    db.session.commit()
                    
                    if count > 0:
                        flash(f'Success! Indexed {count} items. (Sample: {sample_item})', 'success')
                    else:
                        flash(f'Header found at Row {header_row+1}, but found 0 items. Check column positions.', 'warning')

                except Exception as e:
                    print(f"Parser Error: {e}")
                    flash('File uploaded, but indexing failed.', 'warning')

            return redirect(url_for('admin.dashboard'))
    return render_template('upload.html')



# --- VIEW FILE (RAW MODE) ---
@admin_bp.route('/view_file/<int:file_id>')
@login_required
def view_file(file_id):
    q = Quotation.query.get_or_404(file_id)
    path = os.path.join(current_app.root_path, 'static', 'uploads', q.filename)
    if q.filename.endswith(('xlsx', 'xls', 'csv')):
        try:
            if q.filename.endswith('.csv'): 
                df = pd.read_csv(path, header=None, engine='python', on_bad_lines='skip')
            else: 
                df = pd.read_excel(path, header=None)
            
            cols = [chr(65+i) if i < 26 else f"Col{i+1}" for i in range(len(df.columns))]
            return render_template('excel_view.html', filename=q.filename, columns=cols, data=df.fillna('').values.tolist())
        except: 
            pass
    return redirect(url_for('admin.download_file', file_id=file_id))



@admin_bp.route('/download/<int:file_id>')
@login_required
def download_file(file_id):
    q = Quotation.query.get_or_404(file_id)
    return send_from_directory(os.path.join(current_app.root_path, 'static', 'uploads'), q.filename, as_attachment=True)



# --- ASSIGNED ---
@admin_bp.route('/assigned', methods=['GET', 'POST'])
@login_required
def assigned():
    if request.method == 'POST' and 'assign_task' in request.form:
        if current_user.role != 'Admin': return redirect(url_for('admin.dashboard'))
        title, desc, emp_id, deadline = request.form.get('title'), request.form.get('description'), request.form.get('employee_id'), request.form.get('deadline')
        if title and emp_id:
