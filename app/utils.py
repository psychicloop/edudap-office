
import os
import re
import uuid
from functools import wraps
from flask import current_app, abort
from werkzeug.utils import secure_filename

ALLOWED = {'pdf','xls','xlsx','csv','png','jpg','jpeg'}

def allowed_file(filename:str)->bool:
    return '.' in filename and filename.rsplit('.',1)[1].lower() in ALLOWED

def save_upload(file_storage, subdir:str)->str:
    if not file_storage or file_storage.filename == '':
        return ''
    ext = file_storage.filename.rsplit('.',1)[1].lower()
    if not allowed_file(file_storage.filename) and subdir != 'quotation_images':
        raise ValueError('File type not allowed')
    if subdir == 'quotation_images' and ext not in {'png','jpg','jpeg'}:
        raise ValueError('Only images allowed for picture updates')
    fname = f"{uuid.uuid4().hex}.{ext}"
    target_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], subdir)
    os.makedirs(target_dir, exist_ok=True)
    path = os.path.join(target_dir, secure_filename(fname))
    file_storage.save(path)
    return os.path.relpath(path, start=os.path.dirname(current_app.root_path))

def role_required(role):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            from flask_login import current_user
            if not current_user.is_authenticated:
                abort(401)
            if str(current_user.role) != role:
                abort(403)
            return f(*args, **kwargs)
        return wrapper
    return decorator

CAS_REGEX = re.compile(r"\d{2,7}-\d{2}-\d")
