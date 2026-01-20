from . import db
from flask_login import UserMixin
from datetime import datetime

# --- ALL ENUMS ---
class AttendanceType:
    PRESENT, ABSENT, HALF_DAY = 'Present', 'Absent', 'Half Day'

class HolidayStatus:
    PENDING, APPROVED, REJECTED = 'Pending', 'Approved', 'Rejected'

class ExpenseStatus:
    PENDING, APPROVED, REJECTED = 'Pending', 'Approved', 'Rejected'

class TodoStatus:
    PENDING, COMPLETED = 'Pending', 'Completed'

# --- THE ROLE MODEL (Missing piece causing current crash) ---
class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

# --- THE USER MODEL ---
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    role = db.Column(db.String(50), default='Employee')
    password_hash = db.Column(db.String(200), nullable=False)

# --- ALL SUPPORTING MODELS ---
class Quotation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(200), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref='quotations')

class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), default=ExpenseStatus.PENDING)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref='expenses')

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), default=AttendanceType.ABSENT)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref='attendance_records')

class HolidayRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    reason = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(20), default=HolidayStatus.PENDING)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref='holiday_requests')

class LocationPing(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', backref='pings')

class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(20), default=TodoStatus.PENDING)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref='todos')
