from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from datetime import datetime
from . import db
from .models import HolidayRequest, HolidayStatus

leave_bp = Blueprint('leave', __name__, url_prefix='/leave')

@leave_bp.route('/')
@login_required
def index():
    # This matches url_for('leave.index')
    my_leaves = HolidayRequest.query.filter_by(user_id=current_user.id).order_by(HolidayRequest.start_date.desc()).all()
    return render_template('leave.html', leaves=my_leaves)

@leave_bp.route('/events')
@login_required
def get_events():
    leaves = HolidayRequest.query.all()
    events = []
    for l in leaves:
        color = '#ffc107'
        if l.status == HolidayStatus.APPROVED: color = '#28a745'
        elif l.status == HolidayStatus.REJECTED: color = '#dc3545'
        
        events.append({
            'title': f"{l.user.username} ({l.status})",
            'start': l.start_date.isoformat(),
            'end': l.end_date.isoformat(),
            'color': color
        })
    return jsonify(events)

@leave_bp.route('/request', methods=['POST'])
@login_required
def request_leave():
    start_date = request.form.get('start_date')
    end_date = request.form.get('end_date')
    leave_type = request.form.get('leave_type')
    reason = request.form.get('reason')

    if start_date and end_date:
        full_reason = f"[{leave_type}] {reason}"
        new_leave = HolidayRequest(
            user_id=current_user.id,
            start_date=datetime.strptime(start_date, '%Y-%m-%d'),
            end_date=datetime.strptime(end_date, '%Y-%m-%d'),
            reason=full_reason,
            status=HolidayStatus.PENDING
        )
        db.session.add(new_leave)
        db.session.commit()
        flash('Leave requested successfully!', 'success')
    else:
        flash('Invalid dates', 'danger')
        
    return redirect(url_for('leave.index'))
