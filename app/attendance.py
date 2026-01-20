from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime, date
from . import db
from .models import Attendance, AttendanceType

attendance_bp = Blueprint('attendance', __name__, url_prefix='/attendance')

@attendance_bp.route('/')
@login_required
def check_in():
    # FIX: We use 'date' to sort, because 'timestamp' does not exist in your database
    recs = Attendance.query.filter_by(user_id=current_user.id).order_by(Attendance.date.desc()).limit(30).all()
    
    # Check if checked in today
    today_rec = Attendance.query.filter_by(user_id=current_user.id, date=date.today()).first()
    checked_in = (today_rec is not None)
    checked_out = (today_rec.check_out_time is not None) if today_rec else False
    
    return render_template('attendance.html', records=recs, checked_in=checked_in, checked_out=checked_out)

@attendance_bp.route('/mark', methods=['POST'])
@login_required
def mark():
    action = request.form.get('action')
    now = datetime.now()
    today = date.today()
    
    record = Attendance.query.filter_by(user_id=current_user.id, date=today).first()
    
    if action == 'in':
        if not record:
            new_rec = Attendance(user_id=current_user.id, date=today, check_in_time=now, status=AttendanceType.PRESENT)
            db.session.add(new_rec)
            db.session.commit()
            flash('Checked In successfully!', 'success')
    elif action == 'out':
        if record and not record.check_out_time:
            record.check_out_time = now
            db.session.commit()
            flash('Checked Out successfully!', 'success')
            
    return redirect(url_for('attendance.check_in'))
