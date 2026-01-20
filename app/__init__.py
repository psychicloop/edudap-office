from flask import Flask, redirect, url_for, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from sqlalchemy import text  # <--- IMPORT THIS
import os

# -------------------------
# EXTENSIONS (GLOBAL SINGLETONS)
# -------------------------
db = SQLAlchemy()
login_manager = LoginManager()   

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY", "change-me")
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL", "sqlite:///app.db")
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # -------------------------
    # CONFIGURE UPLOAD FOLDER
    # -------------------------
    base_dir = os.path.abspath(os.path.dirname(__file__))
    upload_folder = os.path.join(base_dir, '..', 'uploads')
    app.config['UPLOAD_FOLDER'] = upload_folder
    
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)

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
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

    # -------------------------
    # ROOT REDIRECT
    # -------------------------
    @app.route("/")
    def root():
        return redirect(url_for("auth.login"))

    # -------------------------
    # CREATE TABLES & FIX SEARCH TABLE
    # -------------------------
    with app.app_context():
        # 1. Create standard tables
        db.create_all()
        
        # 2. MANUALLY Create the missing Search Table (FTS)
        # We wrap this in a try-except block to prevent crashes if it already exists or errors out
        try:
            db.session.execute(text("""
                CREATE VIRTUAL TABLE IF NOT EXISTS quotation_fts USING fts5(
                    parsed_text, 
                    brand, 
                    make, 
                    cas_no, 
                    product_name, 
                    instrument, 
                    chemical, 
                    reagent, 
                    kit, 
                    media
                );
            """))
            db.session.commit()
            print("Search table 'quotation_fts' checked/created successfully.")
        except Exception as e:
            print(f"Warning: Could not create FTS table. Search might fail. Error: {e}")

    return app
