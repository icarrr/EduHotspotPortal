#!/usr/bin/env python
"""
Python-based scheduler for EduHotspotPortal
Runs expire_users.check() periodically without needing system cron
"""

import time
import threading
from datetime import datetime
from app import create_app
from app.models import HotspotUser, AuditLog, db
from app.utils.mikrotik import get_mikrotik_client

# Configuration
CHECK_INTERVAL_HOURS = 1  # Run every 1 hour
CHECK_INTERVAL_SECONDS = CHECK_INTERVAL_HOURS * 60 * 60


def expire_users():
    """Check and expire TRIAL users whose expiration date has passed"""
    app = create_app()

    with app.app_context():
        now = datetime.utcnow()

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

        print(f"[{datetime.utcnow()}] Expiration check complete")


def scheduler_loop():
    """Main scheduler loop - runs every CHECK_INTERVAL_HOURS"""
    print(f"[{datetime.utcnow()}] Python scheduler started")
    print(f"Checking every {CHECK_INTERVAL_HOURS} hour(s) for expired trial users...")
    print("-" * 60)

    while True:
        try:
            expire_users()
        except Exception as e:
            print(f"[{datetime.utcnow()}] Scheduler error: {str(e)}")

        # Wait for next check
        print(f"\nNext check in {CHECK_INTERVAL_HOURS} hour(s)...")
        time.sleep(CHECK_INTERVAL_SECONDS)


def run_once():
    """Run expiration check once (for testing)"""
    print(f"[{datetime.utcnow()}] Running one-time expiration check...")
    expire_users()


if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == '--once':
        # Run once and exit (for manual testing)
        run_once()
    elif len(sys.argv) > 1 and sys.argv[1] == '--interval':
        # Custom interval in minutes
        interval = int(sys.argv[2]) if len(sys.argv) > 2 else 60
        CHECK_INTERVAL_SECONDS = interval * 60
        print(f"Using custom interval: {interval} minutes")
        scheduler_loop()
    else:
        # Run as daemon (default behavior)
        # Run immediately on start
        expire_users()
        # Then run on schedule
        scheduler_loop()
