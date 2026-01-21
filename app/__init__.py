from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os

# Initialize Extensions
db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    
    # --- 1. SESSION & SECURITY HARDENING (Critical Fixes) ---
    # Stable Secret Key (Must be set in Render Env for production)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'edudap-persistent-dev-key')
    
    # Cookie Security Flags (Prevents session bleeding/dropping)
    app.config['SESSION_COOKIE_NAME'] = 'edudap_session'
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SECURE'] = True # Render serves HTTPS
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    
    # Database Config
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///db.sqlite3')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize Plugins
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'

    # User Loader
    from .models import User
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # --- 2. ANTI-CACHING HEADERS (Prevents "Stale" Dashboard) ---
    @app.after_request
    def add_no_cache_headers(resp):
        # Only prevent caching on HTML pages, let static assets cache
        if 'text/html' in resp.headers.get('Content-Type', ''):
            resp.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
            resp.headers['Pragma'] = 'no-cache'
            resp.headers['Expires'] = '0'
        return resp

    # Register Blueprints
    from .auth import auth_bp
    from .admin import admin_bp
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    
    # Root Redirect
    from flask import redirect, url_for
    @app.route('/')
    def index():
        return redirect(url_for('admin.dashboard'))

    # Create Tables
    with app.app_context():
        db.create_all()

    return app
