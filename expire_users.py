#!/usr/bin/env python
"""
Auto-expire task for EduHotspotPortal
Checks for expired TRIAL users and disables them in both MikroTik and local DB
Should be run periodically (e.g., via cron job every hour)
"""
from app import create_app
from app.models import HotspotUser, AuditLog, db
from app.utils.mikrotik import get_mikrotik_client
from datetime import datetime, timezone

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

if __name__ == '__main__':
    expire_users()
