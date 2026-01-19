
from apscheduler.schedulers.background import BackgroundScheduler
from . import db
from .models import Todo, Notification, User
from .mailer import send_email
from datetime import datetime

scheduler_instance = None

def init_scheduler(app):
    global scheduler_instance
    if scheduler_instance:
        return scheduler_instance
    scheduler_instance = BackgroundScheduler()
    scheduler_instance.start()
    return scheduler_instance


def _notify(user_id:int, title:str, body:str):
    n = Notification(user_id=user_id, title=title, body=body)
    db.session.add(n)
    db.session.commit()
    user = User.query.get(user_id)
    if user and user.email:
        send_email(user.email, title, body)


def schedule_reminder(todo_id:int, run_at:datetime):
    if not run_at:
        return
    def job():
        todo = Todo.query.get(todo_id)
        if not todo:
            return
        _notify(todo.assignee_id, f"Reminder: {todo.title}", f"Task is due at {todo.due_at}")
    scheduler_instance.add_job(job, 'date', run_date=run_at, id=f'todo-{todo_id}-{run_at.timestamp()}')


def rehydrate_reminders(sched):
    now = datetime.utcnow()
    for t in Todo.query.filter(Todo.reminder_at != None, Todo.reminder_at > now).all():
        schedule_reminder(t.id, t.reminder_at)
