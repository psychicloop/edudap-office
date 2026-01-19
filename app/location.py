
from flask import Blueprint, request, jsonify, render_template
from flask_login import login_required, current_user
from .models import LocationPing, Role
from . import db

location_bp = Blueprint('location', __name__)

@location_bp.route('/')
@login_required
def my_location():
    pings = LocationPing.query.filter_by(user_id=current_user.id).order_by(LocationPing.captured_at.desc()).limit(100).all()
    return render_template('location.html', pings=pings)

@location_bp.route('/ping', methods=['POST'])
@login_required
def ping():
    data = request.get_json(force=True)
    lat = data.get('lat')
    lon = data.get('lon')
    acc = data.get('accuracy') or data.get('accuracy_m')
    if lat is None or lon is None:
        return jsonify({'ok': False, 'error': 'lat/lon required'}), 400
    p = LocationPing(user_id=current_user.id, lat=lat, lon=lon, accuracy_m=acc)
    db.session.add(p)
    db.session.commit()
    return jsonify({'ok': True})

@location_bp.route('/admin/latest')
@login_required
def latest():
    if current_user.role != Role.ADMIN:
        return jsonify({'error':'forbidden'}), 403
    from sqlalchemy import func
    sub = db.session.query(LocationPing.user_id, func.max(LocationPing.captured_at).label('mx')).group_by(LocationPing.user_id).subquery()
    q = db.session.query(LocationPing).join(sub, (LocationPing.user_id==sub.c.user_id) & (LocationPing.captured_at==sub.c.mx)).all()
    payload = [{'user_id': p.user_id, 'lat': p.lat, 'lon': p.lon, 'captured_at': p.captured_at.isoformat()} for p in q]
    return render_template('admin_locations.html', latest=payload)
