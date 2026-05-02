from flask import Blueprint, render_template
from flask_login import login_required
from app.decorators import operator_required
from app.utils.mikrotik import get_mikrotik_client
from app.models import HotspotUser, db
from datetime import datetime

bp = Blueprint('main', __name__)


@bp.route('/')
@login_required
def dashboard():
    mikrotik = get_mikrotik_client()
    mikrotik_connected = mikrotik.connect()

    # Get data from MikroTik (only if connected)
    total_users = 0
    online_users = 0
    disabled_users = 0

    if mikrotik_connected:
        hotspot_users = mikrotik.get_hotspot_users()
        active_sessions = mikrotik.get_active_sessions()

        total_users = len(hotspot_users)
        online_users = len(active_sessions)

        # Count disabled users from MikroTik data
        disabled_users = sum(1 for u in hotspot_users if u.get('disabled') == 'true')

        # Sync users to local DB for tracking (creation dates, etc.)
        sync_users_to_db(hotspot_users)
        mikrotik.disconnect()

    # New users today (from local DB)
    new_today = HotspotUser.query.filter(
        HotspotUser.created_at >= datetime.now().date()
    ).count()

    return render_template('main/dashboard.html',
                           total_users=total_users,
                           online_users=online_users,
                           disabled_users=disabled_users,
                           new_today=new_today,
                           mikrotik_connected=mikrotik_connected)


def sync_users_to_db(mikrotik_users):
    """Sync MikroTik users to local DB for tracking"""
    for mu in mikrotik_users:
        username = mu.get('name')
        existing = HotspotUser.query.filter_by(username=username).first()
        if not existing:
            user = HotspotUser(
                username=username,
                name=mu.get('comment', '').replace('role:', '') if mu.get('comment') else '',
                role=mu.get('comment', '').replace('role:', '') if mu.get('comment') else 'siswa',
                profile=mu.get('profile', ''),
                status='disabled' if mu.get('disabled') == 'true' else 'active'
            )
            db.session.add(user)
    db.session.commit()
