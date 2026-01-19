
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from .models import Attendance, AttendanceType
from . import db

attendance_bp = Blueprint('attendance', __name__)

@attendance_bp.route('/')
@login_required
def my_attendance():
    recs = Attendance.query.filter_by(user_id=current_user.id).order_by(Attendance.timestamp.desc()).limit(100).all()
    return render_template('attendance.html', records=recs)

@attendance_bp.route('/check-in', methods=['POST'])
@login_required
def check_in():
    lat = request.form.get('lat', type=float)
    lon = request.form.get('lon', type=float)
    note = request.form.get('note')
    a = Attendance(user_id=current_user.id, type=AttendanceType.CHECK_IN.value, lat=lat, lon=lon, note=note)
    db.session.add(a)
    db.session.commit()
    flash('Checked in','success')
    return redirect(url_for('attendance.my_attendance'))

@attendance_bp.route('/check-out', methods=['POST'])
@login_required
def check_out():
    lat = request.form.get('lat', type=float)
    lon = request.form.get('lon', type=float)
    note = request.form.get('note')
    a = Attendance(user_id=current_user.id, type=AttendanceType.CHECK_OUT.value, lat=lat, lon=lon, note=note)
    db.session.add(a)
    db.session.commit()
    flash('Checked out','success')
    return redirect(url_for('attendance.my_attendance'))
