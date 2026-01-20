from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime
from . import db
from .models import Todo, TodoStatus

todos_bp = Blueprint('todos', __name__, url_prefix='/todos')

@todos_bp.route('/')
@login_required
def my_todos():
    # Sort by due date (soonest first)
    my_todos = Todo.query.filter_by(user_id=current_user.id).order_by(Todo.due_date.asc()).all()
    # Pass 'now' to template so we can calculate overdue tasks
    return render_template('todos.html', todos=my_todos, now=datetime.utcnow())

@todos_bp.route('/add', methods=['POST'])
@login_required
def add():
    title = request.form.get('title')
    priority = request.form.get('priority')
    due_date_str = request.form.get('due_date') # Get date from form
    
    if title:
        new_todo = Todo(
            title=title,
            priority=priority,
            user_id=current_user.id,
            status=TodoStatus.PENDING
        )
        
        # If user picked a date, convert it and save it
        if due_date_str:
            try:
                new_todo.due_date = datetime.strptime(due_date_str, '%Y-%m-%dT%H:%M')
            except ValueError:
                pass # If date format is wrong, ignore it
            
        db.session.add(new_todo)
        db.session.commit()
        flash('Task added!', 'success')
        
    return redirect(url_for('todos.my_todos'))

@todos_bp.route('/complete/<int:id>')
@login_required
def complete(id):
    todo = Todo.query.get_or_404(id)
    if todo.user_id == current_user.id:
        todo.status = TodoStatus.COMPLETED
        db.session.commit()
    return redirect(url_for('todos.my_todos'))

@todos_bp.route('/delete/<int:id>')
@login_required
def delete(id):
    todo = Todo.query.get_or_404(id)
    if todo.user_id == current_user.id:
        db.session.delete(todo)
        db.session.commit()
    return redirect(url_for('todos.my_todos'))
