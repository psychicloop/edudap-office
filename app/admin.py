from flask import Blueprint, render_template
from flask_login import login_required, current_user

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/dashboard')
@login_required
def dashboard():
    # Removed the check for "if current_user.role != 'Admin'"
    # Now ALL logged-in users can see the dashboard.
    return render_template('dashboard.html', user=current_user)
