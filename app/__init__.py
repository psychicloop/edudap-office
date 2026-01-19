
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from dotenv import load_dotenv
from sqlalchemy import text

load_dotenv()

db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()

def create_app():
    app = Flask(__name__)
    # Keep CSRF simple/off by default; you can enable later by setting WTF_CSRF_ENABLED=True
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'change-me')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///app.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # uploads
    app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), '..', 'uploads')
    app.config['MAX_CONTENT_LENGTH'] = 15 * 1024 * 1024

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    login_manager.login_view = 'auth.login'

    from .auth import auth_bp
    from .attendance import attendance_bp
    from .leave import leave_bp
    from .expenses import expenses_bp
    from .location import location_bp
    from .todos import todos_bp
    from .quotations import quotations_bp
    from .admin import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(attendance_bp, url_prefix='/attendance')
    app.register_blueprint(leave_bp, url_prefix='/leave')
    app.register_blueprint(expenses_bp, url_prefix='/expenses')
    app.register_blueprint(location_bp, url_prefix='/location')
    app.register_blueprint(todos_bp, url_prefix='/todos')
    app.register_blueprint(quotations_bp, url_prefix='/quotations')
    app.register_blueprint(admin_bp, url_prefix='/admin')

    with app.app_context():
        from . import models
        db.create_all()

        from .models import User, Role
        admin_email = os.getenv('ADMIN_EMAIL')
        admin_password = os.getenv('ADMIN_PASSWORD')
        if admin_email and admin_password and not User.query.filter_by(email=admin_email).first():
            u = User(name='Admin', email=admin_email, role=Role.ADMIN)
            u.set_password(admin_password)
            db.session.add(u)
            db.session.commit()

        from .search import ensure_fts
        ensure_fts()

        # Ensure image_path exists for quotations
        try:
            db.session.execute(text('ALTER TABLE quotation ADD COLUMN image_path VARCHAR(255)'))
            db.session.commit()
        except Exception:
            db.session.rollback()

        from .scheduler import init_scheduler, rehydrate_reminders
        scheduler = init_scheduler(app)
        rehydrate_reminders(scheduler)

    return app
