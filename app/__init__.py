
from flask import Flask, redirect, url_for, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os

# -------------------------
# EXTENSIONS (GLOBAL SINGLETONS)
# -------------------------
db = SQLAlchemy()
login_manager = LoginManager()   # <-- FIXED: moved to top level


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY", "change-me")
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL", "sqlite:///app.db")
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # -------------------------
    # INITIALIZE EXTENSIONS
    # -------------------------
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    # -------------------------
    # USER LOADER
    # -------------------------
    from .models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # -------------------------
    # BLUEPRINTS
    # -------------------------
    from .auth import auth_bp
    from .attendance import attendance_bp
    from .leave import leave_bp
    from .expenses import expenses_bp
    from .location import location_bp
    from .todos import todos_bp
    from .quotations import quotations_bp
    from .admin import admin_bp

    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(attendance_bp, url_prefix="/attendance")
    app.register_blueprint(leave_bp, url_prefix="/leave")
    app.register_blueprint(expenses_bp, url_prefix="/expenses")
    app.register_blueprint(location_bp, url_prefix="/location")
    app.register_blueprint(todos_bp, url_prefix="/todos")
    app.register_blueprint(quotations_bp, url_prefix="/quotations")
    app.register_blueprint(admin_bp, url_prefix="/admin")

    # -------------------------
    # SERVE UPLOADED FILES
    # -------------------------
    @app.route("/uploads/<path:filename>")
    def uploaded_files(filename):
        uploads_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "uploads"))
        return send_from_directory(uploads_dir, filename)

    # -------------------------
    # ROOT REDIRECT
    # -------------------------
    @app.route("/")
    def root():
        return redirect(url_for("auth.login"))

    return app
