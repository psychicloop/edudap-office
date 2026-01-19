
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from .models import Expense, ExpenseStatus, Role
from . import db
from .utils import save_upload

expenses_bp = Blueprint('expenses', __name__)

@expenses_bp.route('/')
@login_required
def my_expenses():
    recs = Expense.query.filter_by(user_id=current_user.id).order_by(Expense.submitted_at.desc()).all()
    return render_template('expenses.html', records=recs)

@expenses_bp.route('/submit', methods=['POST'])
@login_required
def submit_expense():
    amount = request.form.get('amount', type=float)
    currency = request.form.get('currency', 'INR')
    category = request.form.get('category')
    caption = request.form.get('caption')
    file = request.files.get('attachment')
    path = save_upload(file, 'expenses') if file else ''
    e = Expense(user_id=current_user.id, amount=amount, currency=currency, category=category, caption=caption, file_path=path)
    db.session.add(e)
    db.session.commit()
    flash('Expense submitted','success')
    return redirect(url_for('expenses.my_expenses'))

@expenses_bp.route('/manage')
@login_required
def manage():
    if current_user.role != Role.ADMIN:
        flash('Admins only','danger')
        return redirect(url_for('expenses.my_expenses'))
    recs = Expense.query.order_by(Expense.submitted_at.desc()).all()
    return render_template('expenses_manage.html', records=recs)

@expenses_bp.route('/<int:eid>/approve', methods=['POST'])
@login_required
def approve(eid):
    from datetime import datetime
    if current_user.role != Role.ADMIN:
        flash('Admins only','danger')
        return redirect(url_for('expenses.manage'))
    e = Expense.query.get_or_404(eid)
    e.status = ExpenseStatus.APPROVED.value
    e.reviewed_by = current_user.id
    e.reviewed_at = datetime.utcnow()
    db.session.commit()
    flash('Expense approved','success')
    return redirect(url_for('expenses.manage'))

@expenses_bp.route('/<int:eid>/reject', methods=['POST'])
@login_required
def reject(eid):
    from datetime import datetime
    if current_user.role != Role.ADMIN:
        flash('Admins only','danger')
        return redirect(url_for('expenses.manage'))
    e = Expense.query.get_or_404(eid)
    e.status = ExpenseStatus.REJECTED.value
    e.reviewed_by = current_user.id
    e.reviewed_at = datetime.utcnow()
    db.session.commit()
    flash('Expense rejected','warning')
    return redirect(url_for('expenses.manage'))
