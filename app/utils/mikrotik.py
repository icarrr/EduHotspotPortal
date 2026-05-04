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
            api = self.connection.api()
            api('/ip/hotspot/user/add')
            api(f'=name={username}')
            api(f'=password={password}')
            api('=disabled=no')
            if profile:
                api(f'=profile={profile}')
            if role:
                api(f'=comment=role:{role}')
            return True, 'User added successfully'
        except (LibRouterosError, ConnectionClosed) as e:
            return False, str(e)

    def edit_hotspot_user(self, username, **kwargs):
        if not self.connection:
            if not self.connect():
                return False, 'Connection failed'
        try:
            users = self.connection.path('ip', 'hotspot', 'user')
            target_user = None
            for user in users:
                if user.get('name') == username:
                    target_user = user
                    break

            if not target_user:
                return False, 'User not found'

            user_id = target_user['.id']
            
            # Use proper API call syntax
            api = self.connection.api()
            api('/ip/hotspot/user/set')
            api(f'=.id={user_id}')
            if 'password' in kwargs:
                api(f'=password={kwargs["password"]}')
            if 'profile' in kwargs:
                api(f'=profile={kwargs["profile"]}')
            if 'disabled' in kwargs:
                api(f'=disabled={kwargs["disabled"]}')
            if 'mac_address' in kwargs:
                api(f'=mac-address={kwargs["mac_address"]}')
            
            return True, 'User updated successfully'
        except (LibRouterosError, ConnectionClosed) as e:
            return False, str(e)

    def delete_hotspot_user(self, username):
        if not self.connection:
            if not self.connect():
                return False, 'Connection failed'
        try:
            users = self.connection.path('ip', 'hotspot', 'user')
            target_user = None
            for user in users:
                if user.get('name') == username:
                    target_user = user
                    break

            if target_user:
                api = self.connection.api()
                api('/ip/hotspot/user/remove')
                api(f'=.id={target_user[".id"]}')
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
            api = self.connection.api()
            api('/ip/hotspot/active/remove')
            api(f'=.id={session_id}')
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

    def _get_user_by_name(self, users_path, username):
        """Helper method to find a user by name"""
        for user in users_path:
            if user.get('name') == username:
                return user
        return None

    def bind_mac_to_user(self, username, mac_address):
        """Bind MAC address to hotspot user for device binding"""
        if not self.connection:
            if not self.connect():
                return False, 'Connection failed'
        try:
            users = self.connection.path('ip', 'hotspot', 'user')
            target_user = self._get_user_by_name(users, username)
            
            if target_user:
                user_id = target_user['.id']
                api = self.connection.api()
                api('/ip/hotspot/user/set')
                api(f'=.id={user_id}')
                api(f'=mac-address={mac_address}')
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
            target_user = self._get_user_by_name(users, username)
            
            if target_user:
                user_id = target_user['.id']
                api = self.connection.api()
                api('/ip/hotspot/user/set')
                api(f'=.id={user_id}')
                api('=mac-address=')
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
            target_user = self._get_user_by_name(users, username)
            
            if target_user and target_user.get('mac-address'):
                return target_user['mac-address']
            return None
        except (LibRouterosError, ConnectionClosed) as e:
            current_app.logger.error(f'Failed to get user MAC binding: {e}')
            return None


def get_mikrotik_client():
    return MikroTikClient()
