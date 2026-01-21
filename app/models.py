from flask_login import UserMixin
from . import db

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(50), default='Employee')

    @property
    def is_admin(self):
        return self.role == 'Admin'

# --- RACE-SAFE FLAG ---
class SiteFlag(db.Model):
    __tablename__ = "site_flags"
    id = db.Column(db.Integer, primary_key=True)
    # Added index=True for performance/locking
    key = db.Column(db.String(64), unique=True, index=True, nullable=False) 
    value = db.Column(db.String(256))
