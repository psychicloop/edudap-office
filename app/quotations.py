from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from .models import Quotation, Role
from . import db
from .utils import save_upload, CAS_REGEX
from .search import upsert_fts, search_fts
import pandas as pd
from PyPDF2 import PdfReader
import os

quotations_bp = Blueprint('quotations', __name__)

@quotations_bp.route('/')
@login_required
def index():
    q = Quotation.query
    if current_user.role != Role.ADMIN:
        q = q.filter(Quotation.uploaded_by == current_user.id)
    recs = q.order_by(Quotation.uploaded_at.desc()).limit(50).all()
    return render_template('quotations.html', records=recs)

@quotations_bp.route('/upload', methods=['POST'])
@login_required
def upload():
    file = request.files.get('file')
    title = request.form.get('title')
    notes = request.form.get('notes')
    if not file:
        flash('Select a file', 'warning')
        return redirect(url_for('quotations.index'))

    path = save_upload(file, 'quotations')
    mime = file.mimetype
    parsed_text = ''   # ← make sure this is two quotes, not one
    brand = make = cas_no = product_name = instrument = chemical = reagent = kit = media = None

    try:
        ext = file.filename.rsplit('.', 1)[1].lower()
        full_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', path))

        if ext in ('xls', 'xlsx', 'csv'):
            if ext != 'csv':
                # pandas needs openpyxl for xlsx
                df = pd.read_excel(full_path, engine='openpyxl')
            else:
                df = pd.read_csv(full_path)

            cols = {c.lower().strip(): c for c in df.columns}

            def pick(*keys):
                for k in keys:
                    if k in cols:
                        return str(df.iloc[0][cols[k]])
                return None

            brand = pick('brand')
            make = pick('make', 'manufacturer')
            product_name = pick('name', 'product', 'product name')
            instrument = pick('instrument')
            chemical = pick('chemical')
            reagent = pick('reagent')
            kit = pick('kit')
            media = pick('media')
            cas_no = pick('cas', 'cas no', 'cas number')

            parsed_text = '\n'.join(['\t'.join(map(str, row)) for row in df.fillna('').astype(str).values])

        elif ext == 'pdf':
            reader = PdfReader(full_path)
            parsed_text = '\n'.join([(p.extract_text() or '') for p in reader.pages])

        if not cas_no and parsed_text:
            import re
            m = CAS_REGEX.search(parsed_text)
            if m:
                cas_no = m.group(0)

    except Exception as e:
        flash(f'Failed to parse file: {e}', 'danger')

    q = Quotation(
        uploaded_by=current_user.id,
        title=title,
        notes=notes,
        file_path=path,
        mime_type=mime,
        parsed_text=parsed_text,
        brand=brand,
        make=make,
        cas_no=cas_no,
        product_name=product_name,
        instrument=instrument,
        chemical=chemical,
        reagent=reagent,
        kit=kit,
        media=media
    )
    db.session.add(q)
    db.session.commit()
    upsert_fts(q)
    flash('Uploaded', 'success')
    return redirect(url_for('quotations.index'))

@quotations_bp.route('/search')
@login_required
def search():
    q = request.args.get('q', '').strip()
    results = []
    if q:
        results = search_fts(q, limit=100)
        if current_user.role != Role.ADMIN:
            results = [r for r in results if r.uploaded_by == current_user.id]
    return render_template('quotations_search.html', q=q, results=results)

@quotations_bp.route('/bulk-delete', methods=['POST'])
@login_required
def bulk_delete():
    ids = request.form.getlist('ids') or (request.form.get('ids') or '').split(',')
    ids = [int(i) for i in ids if str(i).strip().isdigit()]
    if not ids:
        flash('No items selected', 'warning')
        return redirect(url_for('quotations.index'))
    q = Quotation.query.filter(Quotation.id.in_(ids))
    if current_user.role != Role.ADMIN:
        q = q.filter(Quotation.uploaded_by == current_user.id)
    count = 0
    for row in q.all():
        db.session.delete(row)
        count += 1
    db.session.commit()
    flash(f'Deleted {count} item(s)', 'success')
    return redirect(url_for('quotations.index'))

@quotations_bp.route('/bulk-image', methods=['POST'])
@login_required
def bulk_image():
    ids = request.form.getlist('ids') or (request.form.get('ids') or '').split(',')
    ids = [int(i) for i in ids if str(i).strip().isdigit()]
    file = request.files.get('image')
    if not ids:
        flash('No items selected', 'warning')
        return redirect(url_for('quotations.index'))
    if not file:
        flash('Please choose an image', 'warning')
        return redirect(url_for('quotations.index'))
    path = save_upload(file, 'quotation_images')
    q = Quotation.query.filter(Quotation.id.in_(ids))
    if current_user.role != Role.ADMIN:
        q = q.filter(Quotation.uploaded_by == current_user.id)
    count = 0
    for row in q.all():
        row.image_path = path
        count += 1
    db.session.commit()
    flash(f'Updated image for {count} item(s)', 'success')
    return redirect(url_for('quotations.index'))
