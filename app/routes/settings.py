from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from app.decorators import admin_required
from app.models import Setting, AuditLog, RoleProfile, db
from app.utils.mikrotik import get_mikrotik_client

bp = Blueprint('settings', __name__, url_prefix='/settings')


@bp.route('/', methods=['GET', 'POST'])
@login_required
@admin_required
def index():
    if request.method == 'POST':
        settings = {
            'mikrotik_host': request.form.get('mikrotik_host'),
            'mikrotik_port': request.form.get('mikrotik_port'),
            'mikrotik_user': request.form.get('mikrotik_user'),
            'mikrotik_use_ssl': 'true' if request.form.get('mikrotik_use_ssl') else 'false'
        }

        for key, value in settings.items():
            setting = Setting.query.filter_by(key=key).first()
            if setting:
                setting.value = value
            else:
                setting = Setting(key=key, value=value)
                db.session.add(setting)

        password = request.form.get('mikrotik_password')
        if password:
            setting = Setting.query.filter_by(key='mikrotik_password').first()
            if setting:
                setting.value = password
            else:
                setting = Setting(key='mikrotik_password', value=password)
                db.session.add(setting)

        db.session.commit()

        log = AuditLog(operator_id=current_user.id, action='update', target_user='settings',
                       details='Updated MikroTik settings')
        db.session.add(log)
        db.session.commit()

        flash('Settings saved successfully', 'success')
        return redirect(url_for('settings.index'))

    settings = {s.key: s.value for s in Setting.query.all()}
    role_profiles = RoleProfile.query.all()
    return render_template('settings/index.html', settings=settings, role_profiles=role_profiles)


@bp.route('/test-connection')
@login_required
@admin_required
def test_connection():
    mikrotik = get_mikrotik_client()
    if mikrotik.connect():
        mikrotik.disconnect()
        return jsonify({'success': True, 'message': 'Connection successful'})
    
    # Show actual error details
    return jsonify({
        'success': False, 
        'message': f'Connection failed to {mikrotik.host}:{mikrotik.port} (SSL: {mikrotik.use_ssl})',
        'hint': 'Check: 1) API user enabled, 2) API service running, 3) Firewall rules, 4) Correct credentials'
    })


@bp.route('/role-profile/add', methods=['POST'])
@login_required
@admin_required
def add_role_profile():
    role = request.form.get('role')
    profile_name = request.form.get('profile_name')
    description = request.form.get('description', '')

    existing = RoleProfile.query.filter_by(role=role).first()
    if existing:
        existing.profile_name = profile_name
        existing.description = description
    else:
        rp = RoleProfile(role=role, profile_name=profile_name, description=description)
        db.session.add(rp)

    db.session.commit()
    flash('Role-profile mapping saved', 'success')
    return redirect(url_for('settings.index'))

@bp.route('/init-profiles')
@login_required
@admin_required
def init_profiles():
    """Initialize default role-profile mappings based on MikroTik profiles"""
    default_profiles = [
        {'role': 'admin', 'profile_name': 'admin', 'description': 'Administrator access'},
        {'role': 'guru', 'profile_name': 'guru', 'description': 'Teacher hotspot access'},
        {'role': 'siswa', 'profile_name': 'siswa', 'description': 'Student hotspot access'},
        {'role': 'trial', 'profile_name': 'trial', 'description': 'Trial user access'},
    ]

    for prof in default_profiles:
        existing = RoleProfile.query.filter_by(role=prof['role']).first()
        if not existing:
            rp = RoleProfile(role=prof['role'], profile_name=prof['profile_name'], description=prof['description'])
            db.session.add(rp)

    db.session.commit()
    flash('Default role-profile mappings initialized', 'success')
    return redirect(url_for('settings.index'))


@bp.route('/role-profile/delete/<int:id>')
@login_required
@admin_required
def delete_role_profile(id):
    profile = RoleProfile.query.get_or_404(id)
    db.session.delete(profile)
    db.session.commit()
    flash('Role profile mapping deleted', 'success')
    return redirect(url_for('settings.index'))


@bp.route('/expiration-settings', methods=['GET', 'POST'])
@login_required
@admin_required
def expiration_settings():
    """Configure automatic expiration settings"""
    from flask import current_app

    if request.method == 'POST':
        default_expiration_days = request.form.get('default_expiration_days', '')
        auto_expire_enabled = 'true' if request.form.get('auto_expire_enabled') else 'false'

        # Save settings
        settings_to_save = {
            'default_expiration_days': default_expiration_days,
            'auto_expire_enabled': auto_expire_enabled
        }

        for key, value in settings_to_save.items():
            setting = Setting.query.filter_by(key=key).first()
            if setting:
                setting.value = value
            else:
                setting = Setting(key=key, value=value,
                                description='Auto-expiration settings')
                db.session.add(setting)

        db.session.commit()
        flash('Expiration settings updated', 'success')
        return redirect(url_for('settings.expiration_settings'))

    # Get current settings
    settings = {s.key: s.value for s in Setting.query.all()}
    default_expiration_days = settings.get('default_expiration_days', '30')
    auto_expire_enabled = settings.get('auto_expire_enabled', 'false') == 'true'

    return render_template('settings/expiration.html',
                         default_expiration_days=default_expiration_days,
                         auto_expire_enabled=auto_expire_enabled)
