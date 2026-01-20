from flask import Blueprint, render_template, request
from flask_login import login_required, current_user
from .models import Quotation, Expense, db
from sqlalchemy import or_

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/dashboard')
@login_required
def dashboard():
    query = request.args.get('q')
    
    # 1. Base Query: Get my quotations
    sql_query = Quotation.query.filter_by(user_id=current_user.id)

    # 2. Smart Search Logic
    if query:
        # Searches Filename OR Client Name (To:) OR Product Details (Make/Cat No)
        search = f"%{query}%"
        sql_query = sql_query.filter(
            or_(
                Quotation.filename.ilike(search),
                Quotation.client_name.ilike(search),
                Quotation.product_details.ilike(search)
            )
        )
    
    user_quotes = sql_query.order_by(Quotation.uploaded_at.desc()).all()
    user_expenses = Expense.query.filter_by(user_id=current_user.id).all()

    stats = {
        'quote_count': len(user_quotes),
        'expense_total': sum(e.amount for e in user_expenses) if user_expenses else 0,
        'role': current_user.role
    }

    return render_template('dashboard.html', stats=stats, quotes=user_quotes)
