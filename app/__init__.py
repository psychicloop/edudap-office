from flask import Flask, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from werkzeug.middleware.proxy_fix import ProxyFix
from datetime import timedelta, datetime
import os

# Initialize Extensions
db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)

    # --- Config (Security, Proxy, DB) ---
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-change-in-prod-123')
    
    # Cookies
    app.config['SESSION_COOKIE_NAME'] = 'edudap_session'
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SECURE'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    
    # Remember Me
    app.config['REMEMBER_COOKIE_SECURE'] = True
    app.config['REMEMBER_COOKIE_HTTPONLY'] = True
    app.config['REMEMBER_COOKIE_SAMESITE'] = 'Lax'
    app.config['REMEMBER_COOKIE_DURATION'] = timedelta(days=30)

    # Database
    db_url = os.environ.get('DATABASE_URL', 'sqlite:///db.sqlite3')
    if db_url and db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
    }

    # Init
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'

    from .models import User, SiteFlag
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # --- Context Processor (Auto-Year) ---
    @app.context_processor
    def inject_current_year():
        return {"current_year": datetime.utcnow().year}

    # Anti-Cache
    @app.after_request
    def add_no_cache_headers(resp):
        if 'text/html' in resp.headers.get('Content-Type', ''):
            resp.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
            resp.headers['Pragma'] = 'no-cache'
            resp.headers['Expires'] = '0'
        return resp

    # Blueprints
    from .auth import auth_bp
    from .admin import admin_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    
    @app.route('/')
    def index():
        return redirect(url_for('admin.dashboard'))

    # --- BOOTSTRAP: Create DB & Backfill Flag ---
    with app.app_context():
        db.create_all()
        
        try:
            if not SiteFlag.query.filter_by(key='first_admin_created').first():
                if User.query.filter_by(role='Admin').count() > 0:
                    db.session.add(SiteFlag(key='first_admin_created', value='1'))
                    db.session.commit()
                    print("System: Backfilled 'first_admin_created' flag.")
        except Exception:
            db.session.rollback()

    return app
