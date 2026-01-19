
from flask import Blueprint, render_template
from flask_login import login_required, current_user
from .models import Role, Attendance, HolidayRequest, Expense, Todo, Quotation

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.role != Role.ADMIN:
        return render_template('forbidden.html'), 403
    cards = {
        'attendance_today': Attendance.query.count(),
        'pending_leaves': HolidayRequest.query.filter_by(status='PENDING').count(),
        'pending_expenses': Expense.query.filter_by(status='SUBMITTED').count(),
        'open_todos': Todo.query.filter_by(status='OPEN').count(),
        'quotations': Quotation.query.count(),
    }
    return render_template('dashboard_admin.html', cards=cards)
