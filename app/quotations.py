import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from .models import Quotation, db

quotations_bp = Blueprint('quotations', __name__, url_prefix='/quotations')

@quotations_bp.route('/')
@login_required
def index():
    quotes = Quotation.query.all()
    return render_template('quotations.html', quotations=quotes)

@quotations_bp.route('/upload', methods=['POST'])
@login_required
def upload():
    if 'file' not in request.files:
        flash('No file part', 'danger')
        return redirect(request.url)
    
    file = request.files['file']
    if file.filename == '':
        flash('No selected file', 'danger')
        return redirect(request.url)

    if file:
        filename = secure_filename(file.filename)
        # FIX: We only use 'filename' and 'user_id' to match models.py exactly
        new_quote = Quotation(
            filename=filename,
            user_id=current_user.id
        )
        db.session.add(new_quote)
        db.session.commit()
        
        # Save physical file to static folder
        upload_path = os.path.join(current_app.root_path, 'static/uploads/quotations')
        if not os.path.exists(upload_path):
            os.makedirs(upload_path)
        file.save(os.path.join(upload_path, filename))
        
        flash('Quotation uploaded successfully!', 'success')
        return redirect(url_for('quotations.index'))

@quotations_bp.route('/delete/<int:id>')
@login_required
def delete(id):
    quote = Quotation.query.get_or_404(id)
    db.session.delete(quote)
    db.session.commit()
    flash('Quotation deleted', 'info')
    return redirect(url_for('quotations.index'))
