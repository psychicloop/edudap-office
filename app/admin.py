from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from .models import User, Quotation, Expense, Attendance, db

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/dashboard')
@login_required
def dashboard():
    # We pull data safely. If nothing exists, it returns an empty list instead of crashing.
    user_quotations = Quotation.query.filter_by(user_id=current_user.id).all()
    user_expenses = Expense.query.filter_by(user_id=current_user.id).all()
    
    # Summary stats for the boxes on top
    stats = {
        'total_quotes': len(user_quotations),
        'total_expenses': sum(e.amount for e in user_expenses) if user_expenses else 0,
        'role': current_user.role
    }

    return render_template('dashboard.html', stats=stats, quotes=user_quotations)
