from flask_login import UserMixin
from . import db
from datetime import datetime

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(50), default='Employee')
    @property
    def is_admin(self): return self.role == 'Admin'

class SiteFlag(db.Model):
    __tablename__ = "site_flags"
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(64), unique=True, index=True, nullable=False)
    value = db.Column(db.String(256))

# --- LIVE BUSINESS MODELS ---
class Quotation(db.Model):
    __tablename__ = 'quotations'
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(50))
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    uploaded_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    client_name = db.Column(db.String(255))
    uploader = db.relationship('User', backref='uploads')
    products = db.relationship('ProductData', backref='quotation', cascade="all, delete-orphan")

class ProductData(db.Model):
    __tablename__ = 'product_data'
    id = db.Column(db.Integer, primary_key=True)
    quotation_id = db.Column(db.Integer, db.ForeignKey('quotations.id'))
    cat_no = db.Column(db.String(100), index=True)
    item_description = db.Column(db.Text)
    make = db.Column(db.String(100))
    rate = db.Column(db.String(50))
