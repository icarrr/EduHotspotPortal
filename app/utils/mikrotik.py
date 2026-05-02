from librouteros import connect
from librouteros.exceptions import LibRouterosError, ConnectionClosed
from app.models import Setting, AuditLog, db
from flask import current_app


class MikroTikClient:
    def __init__(self):
        self.connection = None
        self._load_settings()

    def _load_settings(self):
        settings = {s.key: s.value for s in Setting.query.all()}
        self.host = settings.get('mikrotik_host', '192.168.1.1')
        self.port = int(settings.get('mikrotik_port', '8728'))
        self.username = settings.get('mikrotik_user', 'apiuser')
        self.password = settings.get('mikrotik_password', '')
        self.use_ssl = settings.get('mikrotik_use_ssl', 'false') == 'true'

    def connect(self):
        self._load_settings()
        try:
            self.connection = connect(
                host=self.host,
                port=self.port,
                username=self.username,
                password=self.password,
                ssl_wrapper=self.use_ssl
            )
            return True
        except Exception as e:
            current_app.logger.error(f'MikroTik connection failed: {e}')
            return False

    def disconnect(self):
        if self.connection:
            try:
                self.connection.close()
            except:
                pass
            self.connection = None

    def get_hotspot_users(self):
        if not self.connection:
            if not self.connect():
                return []
        try:
            users = self.connection.path('ip', 'hotspot', 'user')
            return list(users)
        except (LibRouterosError, ConnectionClosed) as e:
            current_app.logger.error(f'Failed to get hotspot users: {e}')
            return []

    def add_hotspot_user(self, username, password, profile=None, role=None):
        if not self.connection:
            if not self.connect():
                return False, 'Connection failed'
        try:
            users = self.connection.path('ip', 'hotspot', 'user')
            params = {
                'name': username,
                'password': password,
                'disabled': 'no'
            }
            if profile:
                params['profile'] = profile
            if role:
                params['comment'] = f'role:{role}'
            users.add(**params)
            return True, 'User added successfully'
        except (LibRouterosError, ConnectionClosed) as e:
            return False, str(e)

    def edit_hotspot_user(self, username, **kwargs):
        if not self.connection:
            if not self.connect():
                return False, 'Connection failed'
        try:
            users = self.connection.path('ip', 'hotspot', 'user')
            user = users.get(name=username)
            if user:
                update_data = {'id': user[0]['.id']}
                if 'password' in kwargs:
                    update_data['password'] = kwargs['password']
                if 'profile' in kwargs:
                    update_data['profile'] = kwargs['profile']
                if 'disabled' in kwargs:
                    update_data['disabled'] = kwargs['disabled']
                users.update(**update_data)
                return True, 'User updated successfully'
            return False, 'User not found'
        except (LibRouterosError, ConnectionClosed) as e:
            return False, str(e)

    def delete_hotspot_user(self, username):
        if not self.connection:
            if not self.connect():
                return False, 'Connection failed'
        try:
            users = self.connection.path('ip', 'hotspot', 'user')
            user = users.get(name=username)
            if user:
                users.remove(user[0]['.id'])
                return True, 'User deleted successfully'
            return False, 'User not found'
        except (LibRouterosError, ConnectionClosed) as e:
            return False, str(e)

    def enable_user(self, username):
        return self.edit_hotspot_user(username, disabled='no')

    def disable_user(self, username):
        return self.edit_hotspot_user(username, disabled='yes')

    def reset_password(self, username, new_password):
        return self.edit_hotspot_user(username, password=new_password)

    def get_active_sessions(self):
        if not self.connection:
            if not self.connect():
                return []
        try:
            sessions = self.connection.path('ip', 'hotspot', 'active')
            return list(sessions)
        except (LibRouterosError, ConnectionClosed) as e:
            current_app.logger.error(f'Failed to get active sessions: {e}')
            return []

    def disconnect_session(self, session_id):
        if not self.connection:
            if not self.connect():
                return False, 'Connection failed'
        try:
            sessions = self.connection.path('ip', 'hotspot', 'active')
            sessions.remove(session_id)
            return True, 'Session disconnected'
        except (LibRouterosError, ConnectionClosed) as e:
            return False, str(e)

    def get_profiles(self):
        if not self.connection:
            if not self.connect():
                return []
        try:
            profiles = self.connection.path('ip', 'hotspot', 'user', 'profile')
            return list(profiles)
        except (LibRouterosError, ConnectionClosed) as e:
            current_app.logger.error(f'Failed to get profiles: {e}')
            return []


def get_mikrotik_client():
    return MikroTikClient()
