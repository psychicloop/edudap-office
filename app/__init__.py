from flask import Flask, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from werkzeug.middleware.proxy_fix import ProxyFix
from datetime import timedelta
import os

# Initialize Extensions
db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)

    # --- 1. PROXY FIX (Critical for Render HTTPS) ---
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

    # --- 2. SECURITY & COOKIES ---
    # Use a stable SECRET_KEY from environment in production
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-change-in-prod-123')

    # Session Cookie Settings
    app.config['SESSION_COOKIE_NAME'] = 'edudap_session'
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SECURE'] = True  # HTTPS on Render
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

    # Remember-Me Cookie Settings (Flask-Login)
    app.config['REMEMBER_COOKIE_SECURE'] = True
    app.config['REMEMBER_COOKIE_HTTPONLY'] = True
    app.config['REMEMBER_COOKIE_SAMESITE'] = 'Lax'
    app.config['REMEMBER_COOKIE_DURATION'] = timedelta(days=30)  # <-- timedelta

    # --- 3. DATABASE CONFIG (Render Postgres Ready) ---
    db_url = os.environ.get('DATABASE_URL', 'sqlite:///db.sqlite3')

    # Render gives 'postgres://', SQLAlchemy needs 'postgresql://'
    if db_url and db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)

    app.config['SQLALCHEMY_DATABASE_URI'] = db_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Connection resilience (cloud-friendly)
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        "pool_pre_ping": True,
        "pool_recycle": 300,  # seconds
    }

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

    # --- 4. ANTI-CACHING HEADERS ---
    @app.after_request
    def add_no_cache_headers(resp):
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
    @app.route('/')
    def index():
        return redirect(url_for('admin.dashboard'))

    # For prototyping; prefer Flask-Migrate in production
    with app.app_context():
        db.create_all()

    return app
