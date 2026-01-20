from . import db
from flask_login import UserMixin
from datetime import datetime

# --- ENUMS ---
class AttendanceType:
    PRESENT, ABSENT, HALF_DAY = 'Present', 'Absent', 'Half Day'

class HolidayStatus:
    PENDING, APPROVED, REJECTED = 'Pending', 'Approved', 'Rejected'

class TodoStatus:
    PENDING, COMPLETED = 'Pending', 'Completed'

class Priority:
    LOW, MEDIUM, HIGH = 'Low', 'Medium', 'High'

class ExpenseStatus:
    PENDING, APPROVED, REJECTED = 'Pending', 'Approved', 'Rejected'

# --- MODELS ---
class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    role = db.Column(db.String(50), default='Employee')
    password_hash = db.Column(db.String(200), nullable=False)

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
    receipt_filename = db.Column(db.String(200), nullable=True)
    caption = db.Column(db.String(200), nullable=True)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default=ExpenseStatus.PENDING)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref='expenses')

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    check_in_time = db.Column(db.DateTime, nullable=True)
    check_out_time = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), default=AttendanceType.ABSENT)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref='attendance_records')

class HolidayRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    reason = db.Column(db.String(200), nullable=False
