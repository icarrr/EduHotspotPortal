from app import create_app, db
from config import config
from app.models import *

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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
