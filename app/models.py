
from datetime import datetime
from enum import Enum
from flask_login import UserMixin
from . import db
from werkzeug.security import generate_password_hash, check_password_hash


# -------------------------
# ROLE ENUM
# -------------------------
class Role(str, Enum):
    ADMIN = 'ADMIN'
    EMPLOYEE = 'EMPLOYEE'


# -------------------------
# USER MODEL
# -------------------------
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.String(16), default=Role.EMPLOYEE.value, nullable=False)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    phone = db.Column(db.String(50))
    password_hash = db.Column(db.String(255), nullable=False)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def get_id(self):
        return str(self.id)


# -------------------------
# ATTENDANCE
# -------------------------
class AttendanceType(str, Enum):
    CHECK_IN = 'CHECK_IN'
    CHECK_OUT = 'CHECK_OUT'


class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    type = db.Column(db.String(16), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    lat = db.Column(db.Float)
    lon = db.Column(db.Float)
    note = db.Column(db.String(255))


# -------------------------
# HOLIDAY REQUESTS
# -------------------------
class HolidayStatus(str, Enum):
    PENDING = 'PENDING'
    APPROVED = 'APPROVED'
    REJECTED = 'REJECTED'


class HolidayRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    leave_type = db.Column(db.String(50))
    reason = db.Column(db.Text)
    status = db.Column(db.String(16), default=HolidayStatus.PENDING.value)
    decided_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    decided_at = db.Column(db.DateTime)


# -------------------------
# EXPENSES
# -------------------------
class ExpenseStatus(str, Enum):
    SUBMITTED = 'SUBMITTED'
    APPROVED = 'APPROVED'
    REJECTED = 'REJECTED'


class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(10), default='INR')
    category = db.Column(db.String(50))
    caption = db.Column(db.String(255))
    file_path = db.Column(db.String(255))
    status = db.Column(db.String(16), default=ExpenseStatus.SUBMITTED.value)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    reviewed_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    reviewed_at = db.Column(db.DateTime)


# -------------------------
# LOCATION
# -------------------------
class LocationPing(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    lat = db.Column(db.Float, nullable=False)
    lon = db.Column(db.Float, nullable=False)
    accuracy_m = db.Column(db.Float)
    captured_at = db.Column(db.DateTime, default=datetime.utcnow)


# -------------------------
# TODOS
# -------------------------
class TodoStatus(str, Enum):
    OPEN = 'OPEN'
    IN_PROGRESS = 'IN_PROGRESS'
    DONE = 'DONE'


class Priority(str, Enum):
    LOW = 'LOW'
    MED = 'MED'
    HIGH = 'HIGH'


class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    assignee_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    due_at = db.Column(db.DateTime)
    reminder_at = db.Column(db.DateTime)
    priority = db.Column(db.String(10), default=Priority.MED.value)
    status = db.Column(db.String(16), default=TodoStatus.OPEN.value)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# -------------------------
# NOTIFICATIONS
# -------------------------
class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(255))
    body = db.Column(db.Text)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# -------------------------
# QUOTATIONS
# -------------------------
class Quotation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uploaded_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    title = db.Column(db.String(255))
    notes = db.Column(db.Text)
    file_path = db.Column(db.String(255))
    mime_type = db.Column(db.String(50))
    parsed_text = db.Column(db.Text)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    brand = db.Column(db.String(120))
    make = db.Column(db.String(120))
    cas_no = db.Column(db.String(50))
    product_name = db.Column(db.String(255))
    instrument = db.Column(db.String(255))
    chemical = db.Column(db.String(255))
    reagent = db.Column(db.String(255))
    kit = db.Column(db.String(255))
    media = db.Column(db.String(255))
    image_path = db.Column(db.String(255))
