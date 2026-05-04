from librouteros import connect
from librouteros.exceptions import LibRouterosError, ConnectionClosed
from app.models import Setting, AuditLog, db
from flask import current_app
import ssl


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
            connect_params = {
                'host': self.host,
                'port': self.port,
                'username': self.username,
                'password': self.password,
            }
            
            if self.use_ssl:
                connect_params['ssl_wrapper'] = ssl.create_default_context
            
            self.connection = connect(**connect_params)
            return True
        except Exception as e:
            current_app.logger.error(f'MikroTik connection failed: {e}')
            current_app.logger.error(f'Host: {self.host}, Port: {self.port}, SSL: {self.use_ssl}')
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
            user_query = list(users.select('.id', 'name').where(name=username))
            if user_query:
                user_id = user_query[0]['.id']
                update_data = {'.id': user_id}
                if 'password' in kwargs:
                    update_data['password'] = kwargs['password']
                if 'profile' in kwargs:
                    update_data['profile'] = kwargs['profile']
                if 'disabled' in kwargs:
                    update_data['disabled'] = kwargs['disabled']
                if 'mac_address' in kwargs:
                    update_data['mac-address'] = kwargs['mac_address']
                users.set(**update_data)
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
            user_query = list(users.select('.id', 'name').where(name=username))
            if user_query:
                user_id = user_query[0]['.id']
                users.remove(user_id)
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

    def bind_mac_to_user(self, username, mac_address):
        """Bind MAC address to hotspot user for device binding"""
        if not self.connection:
            if not self.connect():
                return False, 'Connection failed'
        try:
            users = self.connection.path('ip', 'hotspot', 'user')
            user_query = list(users.select('.id', 'name').where(name=username))
            if user_query:
                user_id = user_query[0]['.id']
                users.set(**{'.id': user_id, 'mac-address': mac_address})
                return True, 'MAC address bound successfully'
            return False, 'User not found'
        except (LibRouterosError, ConnectionClosed) as e:
            return False, str(e)

    def unbind_mac_from_user(self, username):
        """Remove MAC address binding from hotspot user"""
        if not self.connection:
            if not self.connect():
                return False, 'Connection failed'
        try:
            users = self.connection.path('ip', 'hotspot', 'user')
            user_query = list(users.select('.id', 'name').where(name=username))
            if user_query:
                user_id = user_query[0]['.id']
                users.set(**{'.id': user_id, 'mac-address': ''})
                return True, 'MAC address unbound successfully'
            return False, 'User not found'
        except (LibRouterosError, ConnectionClosed) as e:
            return False, str(e)

    def get_user_mac_binding(self, username):
        """Get MAC address binding for a user"""
        if not self.connection:
            if not self.connect():
                return None
        try:
            users = self.connection.path('ip', 'hotspot', 'user')
            user_query = list(users.select('mac-address', 'name').where(name=username))
            if user_query and user_query[0].get('mac-address'):
                return user_query[0]['mac-address']
            return None
        except (LibRouterosError, ConnectionClosed) as e:
            current_app.logger.error(f'Failed to get user MAC binding: {e}')
            return None


def get_mikrotik_client():
    return MikroTikClient()
