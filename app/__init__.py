from flask import Flask, redirect, url_for, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from sqlalchemy import text
import os

# -------------------------
# EXTENSIONS
# -------------------------
db = SQLAlchemy()
login_manager = LoginManager()   

def create_app():
    # -------------------------
    # 1. CALCULATE EXACT PATHS (THE FIX)
    # -------------------------
    # Get the folder where this file (__init__.py) lives
    app_dir = os.path.abspath(os.path.dirname(__file__))
    # Go up one level to find the project root (where static/ and templates/ usually are)
    project_root = os.path.abspath(os.path.join(app_dir, '..'))

    # Define the folders explicitly using the full system path
    # Try finding them in the root first (common structure)
    template_dir = os.path.join(project_root, 'templates')
    static_dir = os.path.join(project_root, 'static')
    upload_dir = os.path.join(project_root, 'uploads')
    
    # Fallback: If they aren't in root, assume they are inside the app folder
    if not os.path.exists(template_dir):
        template_dir = os.path.join(app_dir, 'templates')
    if not os.path.exists(static_dir):
        static_dir = os.path.join(app_dir, 'static')

    # Initialize App with these EXACT paths
    app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)

    app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY", "change-me")
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL", "sqlite:///app.db")
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # -------------------------
    # 2. CONFIGURE UPLOAD FOLDER
    # -------------------------
    app.config['UPLOAD_FOLDER'] = upload_dir
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)

    # -------------------------
    # 3. INITIALIZE EXTENSIONS
    # -------------------------
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    from .models import User
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # -------------------------
    # 4. BLUEPRINTS
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
    # 5. ROUTES
    # -------------------------
    @app.route("/uploads/<path:filename>")
    def uploaded_files(filename):
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

    @app.route("/")
    def root():
        return redirect(url_for("auth.login"))

    # -------------------------
    # 6. DATABASE SETUP
    # -------------------------
    with app.app_context():
        db.create_all()
        try:
            db.session.execute(text("""
                CREATE VIRTUAL TABLE IF NOT EXISTS quotation_fts USING fts5(
                    parsed_text, brand, make, cas_no, product_name, 
                    instrument, chemical, reagent, kit, media
                );
            """))
            db.session.commit()
            print("Search table 'quotation_fts' checked/created successfully.")
        except Exception as e:
            print(f"Warning: FTS table issue (Safe to ignore if search works): {e}")

    return app
