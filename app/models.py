from . import db
from flask_login import UserMixin
from datetime import datetime

# --- ENUMS (Required by other files) ---
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
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    role = db.Column(db.String(50), default='Employee')
    password_hash = db.Column(db.String(200), nullable=False)

class Quotation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(200), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

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

class HolidayRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    reason = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(20), default=HolidayStatus.PENDING)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref='holiday_requests')

class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(20), default=TodoStatus.PENDING)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
