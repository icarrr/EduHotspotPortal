from app import create_app, db
from app.models import *
from app.utils.mikrotik import get_mikrotik_client

import threading
import time
from datetime import datetime, timezone, timedelta
import pytz


STUDENT_CHECK_INTERVAL_MINUTES = 5
STUDENT_CHECK_INTERVAL_SECONDS = STUDENT_CHECK_INTERVAL_MINUTES * 60
TRIAL_CHECK_INTERVAL_HOURS = 1
TRIAL_CHECK_INTERVAL_SECONDS = TRIAL_CHECK_INTERVAL_HOURS * 60 * 60

WITA = pytz.timezone('Asia/Makassar')

STUDENT_LOGIN_START = 7
STUDENT_LOGIN_END = 14


def expire_trial_users():
    """Check and expire TRIAL users whose expiration date has passed"""
    app = create_app()

    with app.app_context():
        now = datetime.now(timezone.utc)

        expired_users = HotspotUser.query.filter(
            HotspotUser.expires_at < now,
            HotspotUser.expires_at.isnot(None),
            HotspotUser.status == 'active',
            HotspotUser.role == 'trial'
        ).all()

        if not expired_users:
            print(f"[{now}] No expired trial users found")
            return

        now = datetime.now(timezone.utc)
        print(f"[{now}] Found {len(expired_users)} expired trial users")

        mikrotik = get_mikrotik_client()

        for user in expired_users:
            try:
                success, message = mikrotik.disable_user(user.username)

                if success:
                    user.status = 'expired'
                    db.session.commit()

                    log = AuditLog(
                        operator_id=1,
                        action='disable',
                        target_user=user.username,
                        details='Auto-expired (trial user)'
                    )
                    db.session.add(log)
                    db.session.commit()

                    print(f"  ✓ Expired trial user: {user.username}")
                else:
                    print(f"  ✗ Failed to expire {user.username}: {message}")

            except Exception as e:
                print(f"  ✗ Error expiring {user.username}: {str(e)}")

        print(f"[{datetime.now(timezone.utc)}] Expiration check complete")


def student_time_control():
    """
    Enforce student access hours (if enabled in settings):
    - >= 07:00 WITA: Enable ALL siswa users
    - >= 14:00 WITA: Disable ALL siswa users + disconnect active sessions
    """
    app = create_app()

    with app.app_context():
        # Check if student time control is enabled
        from app.models import Setting
        enabled_setting = Setting.query.filter_by(key='student_time_control_enabled').first()
        if not enabled_setting or enabled_setting.value != 'true':
            print("  Student time control is DISABLED (toggle in Settings)")
            return

        now_wita = datetime.now(WITA)
        current_hour = now_wita.hour
        print(f"\n[{now_wita.strftime('%Y-%m-%d %H:%M:%S WITA')}] Student time control check (hour={current_hour})")

        mikrotik = get_mikrotik_client()
        if not mikrotik.connect():
            print("  ✗ MikroTik connection failed")
            return

        try:
            all_users = mikrotik.get_hotspot_users()
            siswa_users = [u for u in all_users if str(u.get('profile')) == 'siswa']

            if current_hour >= STUDENT_LOGIN_END or current_hour < STUDENT_LOGIN_START:
                print(f"  Outside school hours ({STUDENT_LOGIN_START}:00-{STUDENT_LOGIN_END}:00). Disabling ALL siswa users...")

                disabled_count = 0
                for user in siswa_users:
                    username = str(user.get('name'))
                    if user.get('disabled') == True:
                        continue

                    success, message = mikrotik.disable_user(username)
                    if success:
                        disabled_count += 1

                        local_user = HotspotUser.query.filter_by(username=username).first()
                        if not local_user:
                            local_user = HotspotUser(username=username, role='siswa')
                            db.session.add(local_user)

                        local_user.status = 'time_disabled'
                        db.session.commit()

                        log = AuditLog(
                            operator_id=1,
                            action='disable',
                            target_user=username,
                            details='Auto-disabled: outside school hours'
                        )
                        db.session.add(log)
                        db.session.commit()

                        print(f"  ✓ Disabled: {username}")
                    else:
                        print(f"  ✗ Failed to disable {username}: {message}")

                active_sessions = mikrotik.get_active_sessions()
                disconnected_count = 0
                for session in active_sessions:
                    session_user = str(session.get('user'))
                    session_profile = None
                    for u in all_users:
                        if str(u.get('name')) == session_user:
                            session_profile = str(u.get('profile'))
                            break

                    if session_profile == 'siswa':
                        session_id = session['.id']
                        success, message = mikrotik.disconnect_session(session_id)
                        if success:
                            disconnected_count += 1
                            print(f"  ✓ Disconnected session: {session_user}")
                        else:
                            print(f"  ✗ Failed to disconnect {session_user}: {message}")

                print(f"  Summary: {disabled_count} disabled, {disconnected_count} sessions disconnected")

            else:
                print(f"  School hours ({STUDENT_LOGIN_START}:00-{STUDENT_LOGIN_END}:00). Enabling ALL siswa users...")

                enabled_count = 0
                for user in siswa_users:
                    username = str(user.get('name'))
                    if user.get('disabled') == True:
                        success, message = mikrotik.enable_user(username)
                        if success:
                            enabled_count += 1

                            local_user = HotspotUser.query.filter_by(username=username).first()
                            if not local_user:
                                local_user = HotspotUser(username=username, role='siswa')
                                db.session.add(local_user)

                            local_user.status = 'active'
                            db.session.commit()

                            log = AuditLog(
                                operator_id=1,
                                action='enable',
                                target_user=username,
                                details='Auto-enabled: school hours started'
                            )
                            db.session.add(log)
                            db.session.commit()

                            print(f"  ✓ Enabled: {username}")
                        else:
                            print(f"  ✗ Failed to enable {username}: {message}")
                    else:
                        print(f"  ✓ Already enabled: {username}")

                print(f"  Summary: {enabled_count} enabled")

        except Exception as e:
            print(f"  ✗ Error: {str(e)}")
        finally:
            mikrotik.disconnect()


def scheduler_loop():
    """Main scheduler loop - runs student check every 5 min, trial check every hour"""
    print(f"[{datetime.now(WITA).strftime('%Y-%m-%d %H:%M:%S WITA')}] Scheduler started")
    print(f"Student time control: every {STUDENT_CHECK_INTERVAL_MINUTES} minutes")
    print(f"Trial user expiration: every {TRIAL_CHECK_INTERVAL_HOURS} hour(s)")
    print("-" * 60)

    last_trial_check = time.time()

    while True:
        try:
            student_time_control()

            now = time.time()
            if now - last_trial_check >= TRIAL_CHECK_INTERVAL_SECONDS:
                expire_trial_users()
                last_trial_check = now
        except Exception as e:
            print(f"[{datetime.now(WITA)}] Scheduler error: {str(e)}")

        print(f"\nNext student check in {STUDENT_CHECK_INTERVAL_MINUTES} minutes...")
        time.sleep(STUDENT_CHECK_INTERVAL_SECONDS)


if __name__ == '__main__':
    app = create_app('development')

    with app.app_context():
        db.create_all()
        if not Operator.query.filter_by(username='admin').first():
            import os
            default_password = os.getenv('DEFAULT_ADMIN_PASSWORD', 'admin123')
            admin = Operator(username='admin', name='Administrator', role='admin_it')
            admin.set_password(default_password)
            db.session.add(admin)
            db.session.commit()
            print(f'Default admin created: admin/{default_password}')

    import pytz
    scheduler_thread = threading.Thread(target=scheduler_loop, daemon=True)
    scheduler_thread.start()

    app.run(host='0.0.0.0', port=7171, debug=True)
