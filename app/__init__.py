from flask import Flask, redirect, url_for
from datetime import datetime  # <--- Added
# ... existing imports ...

def create_app():
    app = Flask(__name__)
    # ... existing config ...

    # --- Context Processor (Auto-Year) ---
    @app.context_processor
    def inject_current_year():
        return {"current_year": datetime.utcnow().year}

    # ... existing blueprints ...
    
    return app
