from . import db
from flask_login import UserMixin
from datetime import datetime

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(50), default='User') 

class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(10), default='INR')
    category = db.Column(db.String(50))
    caption = db.Column(db.Text)
    file_path = db.Column(db.String(200))
    status = db.Column(db.String(20), default='Pending')
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    reviewed_by = db.Column(db.Integer, nullable=True)
    reviewed_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], backref='expenses')

class ExpenseStatus:
    PENDING = 'Pending'
    APPROVED = 'Approved'
    REJECTED = 'Rejected'

class Role:
    ADMIN = 'Admin'
    USER = 'User'

# --- THE FIX IS HERE ---
class Quotation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    
    # We added these to match your Upload Code
    filename = db.Column(db.String(300))
    filepath = db.Column(db.String(500)) 
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    uploader = db.relationship('User', backref='uploads')

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    check_in_time = db.Column(db.DateTime)
    check_out_time = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='Present')
    user = db.relationship('User', backref='attendance')

class Leave(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    reason = db.Column(db.String(200))
    status = db.Column(db.String(20), default='Pending')
    user = db.relationship('User', backref='leaves')
