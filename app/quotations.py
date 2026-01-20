from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
from datetime import datetime
from . import db
from .models import Quotation

quotations_bp = Blueprint('quotations', __name__)

@quotations_bp.route('/')
@login_required
def index():
    # FIXED: Using 'uploaded_at' to match your database
    quotes = Quotation.query.order_by(Quotation.uploaded_at.desc()).all()
    return render_template('quotations.html', quotations=quotes)

@quotations_bp.route('/upload', methods=['POST'])
@login_required
def upload():
    # 1. Check if file is present
    if 'file' not in request.files:
        flash('No file part', 'danger')
        return redirect(url_for('quotations.index'))
        
    file = request.files['file']
    
    # 2. Check if filename is empty
    if file.filename == '':
        flash('No selected file', 'danger')
        return redirect(url_for('quotations.index'))

    if file:
        # 3. Secure the filename
        filename = secure_filename(file.filename)
        save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        file.save(save_path)

        # 4. Save to Database (FIXED: Using 'uploaded_at')
        new_quote = Quotation(
            filename=filename,
            filepath=filename,
            uploaded_at=datetime.utcnow(),
            uploader=current_user
        )
        db.session.add(new_quote)
        db.session.commit()

        flash('File uploaded successfully!', 'success')
        return redirect(url_for('quotations.index'))

    return redirect(url_for('quotations.index'))
