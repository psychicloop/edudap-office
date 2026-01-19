
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from .models import HolidayRequest, HolidayStatus, User, Role
from . import db

leave_bp = Blueprint('leave', __name__)

@leave_bp.route('/')
@login_required
def my_leave():
    myreq = HolidayRequest.query.filter_by(user_id=current_user.id).order_by(HolidayRequest.id.desc()).all()
    return render_template('leave.html', myreq=myreq)

@leave_bp.route('/request', methods=['POST'])
@login_required
def request_leave():
    start_date = request.form.get('start_date')
    end_date = request.form.get('end_date')
    leave_type = request.form.get('leave_type')
    reason = request.form.get('reason')
    r = HolidayRequest(user_id=current_user.id, start_date=datetime.fromisoformat(start_date).date(), end_date=datetime.fromisoformat(end_date).date(), leave_type=leave_type, reason=reason)
    db.session.add(r)
    db.session.commit()
    flash('Leave requested','success')
    return redirect(url_for('leave.my_leave'))

@leave_bp.route('/manage')
@login_required
def manage():
    if current_user.role != Role.ADMIN:
        flash('Admins only','danger')
        return redirect(url_for('leave.my_leave'))
    reqs = HolidayRequest.query.order_by(HolidayRequest.id.desc()).all()
    return render_template('leave_manage.html', reqs=reqs)

@leave_bp.route('/<int:req_id>/approve', methods=['POST'])
@login_required
def approve(req_id):
    if current_user.role != Role.ADMIN:
        flash('Admins only','danger')
        return redirect(url_for('leave.my_leave'))
    r = HolidayRequest.query.get_or_404(req_id)
    r.status = HolidayStatus.APPROVED.value
    r.decided_by = current_user.id
    r.decided_at = datetime.utcnow()
    db.session.commit()
    flash('Approved','success')
    return redirect(url_for('leave.manage'))

@leave_bp.route('/<int:req_id>/reject', methods=['POST'])
@login_required
def reject(req_id):
    if current_user.role != Role.ADMIN:
        flash('Admins only','danger')
        return redirect(url_for('leave.my_leave'))
    r = HolidayRequest.query.get_or_404(req_id)
    r.status = HolidayStatus.REJECTED.value
    r.decided_by = current_user.id
    r.decided_at = datetime.utcnow()
    db.session.commit()
    flash('Rejected','warning')
    return redirect(url_for('leave.manage'))

@leave_bp.route('/calendar')
@login_required
def leave_calendar():
    return render_template('leave_calendar.html')

@leave_bp.route('/events')
@login_required
def leave_events():
    q = HolidayRequest.query
    if current_user.role != Role.ADMIN:
        q = q.filter(HolidayRequest.user_id==current_user.id)
    recs = q.all()

    events = []
    for r in recs:
        u = User.query.get(r.user_id)
        name = u.name if u else f"User {r.user_id}"
        title = f"{name}: {r.leave_type or 'Leave'}"
        end_exclusive = r.end_date + timedelta(days=1) if r.end_date else None
        color = {'PENDING':'#F0AD4E','APPROVED':'#5CB85C','REJECTED':'#D9534F'}.get(r.status, '#6DB9D6')
        events.append({
            'id': r.id,
            'title': title,
            'start': r.start_date.isoformat() if r.start_date else None,
            'end': end_exclusive.isoformat() if end_exclusive else None,
            'allDay': True,
            'color': color,
            'extendedProps': {'status': r.status, 'reason': r.reason or ''}
        })
    return jsonify(events)
