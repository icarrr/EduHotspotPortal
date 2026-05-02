from app import create_app, db
from config import config
from app.models import *

import threading
import time
from datetime import datetime, timezone
from app.utils.mikrotik import get_mikrotik_client

# Configuration
CHECK_INTERVAL_HOURS = 1  # Run every 1 hour
CHECK_INTERVAL_SECONDS = CHECK_INTERVAL_HOURS * 60 * 60


def expire_users():
    """Check and expire TRIAL users whose expiration date has passed"""
    app = create_app()

    with app.app_context():
        now = datetime.now(timezone.utc)

        # Find TRIAL users with expiration date in the past only
        expired_users = HotspotUser.query.filter(
            HotspotUser.expires_at < now,
            HotspotUser.expires_at.isnot(None),
            HotspotUser.status == 'active',
            HotspotUser.role == 'trial'  # Only expire trial users
        ).all()

        if not expired_users:
            print(f"[{now}] No expired trial users found")
            return

        now = datetime.now(timezone.utc)
        print(f"[{now}] Found {len(expired_users)} expired trial users")

        mikrotik = get_mikrotik_client()

        for user in expired_users:
            try:
                # Disable in MikroTik
                success, message = mikrotik.disable_user(user.username)

                if success:
                    # Update local DB
                    user.status = 'expired'
                    db.session.commit()

                    # Log the action
                    log = AuditLog(
                        operator_id=1,  # System user
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


def scheduler_loop():
    """Main scheduler loop - runs every CHECK_INTERVAL_HOURS"""
    print(f"[{datetime.now(timezone.utc)}] Python scheduler started")
    print(f"Checking every {CHECK_INTERVAL_HOURS} hour(s) for expired trial users...")
    print("-" * 60)

    # Run once immediately
    expire_users()

    while True:
        try:
            expire_users()
        except Exception as e:
            print(f"[{datetime.now(timezone.utc)}] Scheduler error: {str(e)}")

        # Wait for next check
        print(f"\nNext check in {CHECK_INTERVAL_HOURS} hour(s)...")
        time.sleep(CHECK_INTERVAL_SECONDS)


if __name__ == '__main__':
    app = create_app('development')

    with app.app_context():
        db.create_all()
        # Create default admin if not exists
        if not Operator.query.filter_by(username='admin').first():
            admin = Operator(username='admin', name='Administrator', role='admin_it')
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print('Default admin created: admin/admin123')

    # Start scheduler in background thread
    print("Starting scheduler in background thread...")
    scheduler_thread = threading.Thread(target=scheduler_loop, daemon=True)
    scheduler_thread.start()

    # Run Flask app in main thread
    app.run(host='0.0.0.0', port=5000, debug=True)
