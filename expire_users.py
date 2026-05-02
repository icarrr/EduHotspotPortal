#!/usr/bin/env python
"""
Auto-expire task for EduHotspotPortal
Checks for expired users and disables them in both MikroTik and local DB
Should be run periodically (e.g., via cron job every hour)
"""
from app import create_app
from app.models import HotspotUser, AuditLog, db
from app.utils.mikrotik import get_mikrotik_client
from datetime import datetime

def expire_users():
    """Check and expire users whose expiration date has passed"""
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
        
        if not expired_users:
            print(f"[{now}] No expired users found")
            return
        
        print(f"[{now}] Found {len(expired_users)} expired users")
        
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
                        details='Auto-expired due to expiration date'
                    )
                    db.session.add(log)
                    db.session.commit()
                    
                    print(f"  ✓ Expired user: {user.username}")
                else:
                    print(f"  ✗ Failed to expire {user.username}: {message}")
                    
            except Exception as e:
                print(f"  ✗ Error expiring {user.username}: {str(e)}")
        
        print(f"[{datetime.utcnow()}] Expiration check complete")

if __name__ == '__main__':
    expire_users()
