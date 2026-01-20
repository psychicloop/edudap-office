from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from . import db
from .models import Todo, TodoStatus, Priority

todos_bp = Blueprint('todos', __name__, url_prefix='/todos')

# FIX: Renamed function from 'index' to 'my_todos' to match your HTML menu
@todos_bp.route('/')
@login_required
def my_todos():
    # Fetch user's todos
    my_todos = Todo.query.filter_by(user_id=current_user.id).order_by(Todo.created_at.desc()).all()
    return render_template('todos.html', todos=my_todos)

@todos_bp.route('/add', methods=['POST'])
@login_required
def add():
    title = request.form.get('title')
    priority = request.form.get('priority')
    
    if title:
        new_todo = Todo(
            title=title,
            priority=priority,
            user_id=current_user.id,
            status=TodoStatus.PENDING
        )
        db.session.add(new_todo)
        db.session.commit()
        flash('Task added!', 'success')
        
    # FIX: Redirects back to 'my_todos'
    return redirect(url_for('todos.my_todos'))

@todos_bp.route('/complete/<int:id>')
@login_required
def complete(id):
    todo = Todo.query.get_or_404(id)
    if todo.user_id == current_user.id:
        todo.status = TodoStatus.COMPLETED
        db.session.commit()
    # FIX: Redirects back to 'my_todos'
    return redirect(url_for('todos.my_todos'))

@todos_bp.route('/delete/<int:id>')
@login_required
def delete(id):
    todo = Todo.query.get_or_404(id)
    if todo.user_id == current_user.id:
        db.session.delete(todo)
        db.session.commit()
    # FIX: Redirects back to 'my_todos'
    return redirect(url_for('todos.my_todos'))
