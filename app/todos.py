
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime
from .models import Todo, TodoStatus, Priority, Role
from . import db
from .scheduler import schedule_reminder


todos_bp = Blueprint('todos', __name__)

@todos_bp.route('/')
@login_required
def my_todos():
    mine = Todo.query.filter_by(assignee_id=current_user.id).order_by(Todo.created_at.desc()).all()
    return render_template('todos.html', mine=mine)

@todos_bp.route('/create', methods=['POST'])
@login_required
def create():
    title = request.form.get('title')
    description = request.form.get('description')
    assignee_id = request.form.get('assignee_id', type=int) or current_user.id
    if assignee_id != current_user.id and current_user.role != Role.ADMIN:
        assignee_id = current_user.id
    due_at = request.form.get('due_at')
    reminder_at = request.form.get('reminder_at')
    priority = request.form.get('priority','MED')
    t = Todo(owner_id=current_user.id, assignee_id=assignee_id, title=title, description=description,
             due_at=datetime.fromisoformat(due_at) if due_at else None,
             reminder_at=datetime.fromisoformat(reminder_at) if reminder_at else None,
             priority=priority)
    db.session.add(t)
    db.session.commit()
    if t.reminder_at:
        schedule_reminder(t.id, t.reminder_at)
    flash('Task created','success')
    return redirect(url_for('todos.my_todos'))

@todos_bp.route('/<int:tid>/status', methods=['POST'])
@login_required
def set_status(tid):
    status = request.form.get('status','OPEN')
    t = Todo.query.get_or_404(tid)
    if t.assignee_id != current_user.id and t.owner_id != current_user.id:
        flash('Not allowed','danger')
        return redirect(url_for('todos.my_todos'))
    t.status = status
    db.session.commit()
    flash('Updated','success')
    return redirect(url_for('todos.my_todos'))
