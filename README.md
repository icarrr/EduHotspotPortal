# EduHotspotPortal (EHP)

A web-based admin panel that lets school hotspot operators manage MikroTik hotspot accounts through a browser instead of Winbox or the CLI.

## Overview

EduHotspotPortal (EHP) is a Flask application that acts as an abstraction layer on top of a MikroTik router's Hotspot feature. It gives non-technical school staff (teachers, lab assistants) a simple interface for creating, editing, disabling, and monitoring hotspot user accounts.

The main workflow is:

1. An operator logs into the web panel.
2. The application talks to the MikroTik router over its API (`librouteros`).
3. Account changes (create, disable, reset, delete) are executed on the router and recorded in a local SQLite audit log.

## Features

- **Dashboard** — summary of hotspot users (total, online, disabled, new today) and live host/session status merged from router data
- **User management** — create, edit, delete, search, and bulk-delete hotspot users
- **Account controls** — one-click enable/disable, reset password, reset traffic counters, force-disconnect active sessions
- **Online session monitoring** — view logged-in devices (host + session merge) and disconnect individual sessions
- **Bulk import (XLSX)** — import users from an Excel file with auto-generated passwords, duplicate skipping, and exportable results
- **Export** — export all hotspot users to XLSX and download the import template
- **MAC binding** — bind or unbind a MAC address to a user (device binding)
- **Expiration** — set per-user expiration dates and a default expiration policy for trial users
- **Automated scheduling** — student time control (auto enable/disable student accounts by time of day) and auto-expiry for expired trial accounts
- **Audit log** — records operator actions (create, update, delete, reset, enable, disable, bulk import, settings changes)
- **Role-based access control (RBAC)** — separate roles for Admin IT and Operator
- **Role–profile mapping** — maps application roles to MikroTik hotspot profiles
- **Settings** — MikroTik connection configuration with a test-connection feature

## Tech Stack

- **Backend:** Python 3.8+, Flask 3.0.0
- **Database:** SQLite (via Flask-SQLAlchemy)
- **Authentication:** Flask-Login, Werkzeug password hashing
- **MikroTik API:** librouteros 3.2.1
- **Excel handling:** openpyxl 3.1.2
- **Scheduling/timezones:** pytz, Python `threading`
- **Frontend:** Bootstrap 5.3 + Tabler Icons (CDN), custom CSS/JS

## Requirements

- Python 3.8+
- A MikroTik router with Hotspot enabled and the API service available (port 8728, or 8729 for SSL)

## Getting Started

### Installation

Clone the repository and set up a virtual environment:

```bash
git clone git@github.com:icarrr/EduHotspotPortal.git
cd EduHotspotPortal

python3 -m venv venv
source venv/bin/activate      # Linux/macOS
# venv\Scripts\activate       # Windows

pip install -r requirements.txt
```

### Configuration

Create your environment file from the template:

```bash
cp .env.example .env
```

The app reads all settings from `.env`. It also reads MikroTik connection settings from the **Settings** page in the UI, which override the routing defaults stored in the database.

### Environment Variables

| Variable | Required | Description |
|---|---|---|
| `FLASK_APP` | No | App entry point (default `run.py`) |
| `FLASK_ENV` | No | Environment name (default `development`) |
| `SECRET_KEY` | Yes* | Flask session signing key. Set a strong random value in production. |
| `DB_PATH` | No | Path to the SQLite database file (default `instance/eduhotspotportal.db`) |
| `DEFAULT_ADMIN_PASSWORD` | No | Password for the default `admin` account created on first run (default `admin123`) |
| `MIKROTIK_HOST` | No | Router IP/hostname (default `192.168.1.1`) |
| `MIKROTIK_PORT` | No | Router API port (default `8728`) |
| `MIKROTIK_USER` | No | Router API username (default `apiuser`) |
| `MIKROTIK_PASSWORD` | No | Router API password (default `apipassword`) |
| `MIKROTIK_USE_SSL` | No | `true` to use the API over SSL on port 8729 (default `false`) |

> **Security:** `SECRET_KEY` and `DEFAULT_ADMIN_PASSWORD` are server-side secrets. Do not commit real values; always use `.env` (which is gitignored).

### Running Locally

```bash
python run.py
```

On first run the app creates the SQLite database and a default administrator account (`admin` / `admin123`) if no operator exists. It also starts the background scheduler thread.

Open `http://127.0.0.1:7171/auth/login` and log in.

> **Important:** Change the default admin password immediately after your first login.

## Project Structure

```
EduHotspotPortal/
├── app/
│   ├── __init__.py          # App factory, blueprint & error-handler registration
│   ├── extensions.py        # SQLAlchemy and Flask-Login setup
│   ├── decorators.py        # RBAC decorators (admin_required, operator_required)
│   ├── models/
│   │   └── __init__.py      # Operator, HotspotUser, RoleProfile, AuditLog, Setting
│   ├── routes/
│   │   ├── auth.py          # Login/logout
│   │   ├── main.py          # Dashboard
│   │   ├── users.py         # User management, import/export, audit logs, operators
│   │   └── settings.py      # MikroTik settings, role-profile mapping, expiration
│   ├── templates/           # Jinja2 templates (Dashboard, users, settings, errors)
│   ├── static/
│   │   ├── css/custom.css
│   │   └── js/custom.js
│   └── utils/
│       └── mikrotik.py      # MikroTik API client (librouteros)
├── config.py                # Environment-based configuration
├── run.py                   # Application entry point + scheduler
├── scheduler.py             # Standalone scheduler (trial user expiry)
├── expire_users.py          # One-shot expiry task (cron-friendly)
├── test_mikrotik.py         # MikroTik connection test script
├── requirements.txt         # Python dependencies
├── .env.example             # Environment variable template
├── ehp-prd.md               # Product Requirements Document
└── AGENTS.md                # Developer/agent guidelines
```

Key directories:

- `app/routes/` — HTTP route handlers grouped by feature area
- `app/models/` — SQLAlchemy models (SQLite tables)
- `app/templates/` — Jinja2 templates rendered by the routes
- `app/utils/mikrotik.py` — the single wrapper around all MikroTik API calls

## Usage

### Roles

| Feature | Admin IT | Operator |
|---|---|---|
| Dashboard | yes | yes |
| User management | yes | yes |
| Online sessions | yes | yes |
| Import / export users | yes | yes |
| MAC binding / expiration | yes | yes |
| Operators | yes | no |
| Audit logs | yes | no |
| Settings | yes | no |

Roles are enforced server-side through `@admin_required` / `@operator_required` decorators plus the sidebar in the base template.

### Importing Users (XLSX)

The import template contains three columns:

| username | nama | role |
|---|---|---|
| `12345` | Budi Santoso | siswa |
| `67890` | Siti Nurhaliza | guru |
| `11111` | Ahmad Staff | trial |

- Password is generated automatically for each imported user (visible in the results page and downloadable as XLSX).
- Duplicate usernames are skipped.
- Unrecognized `role` values default to `siswa`. Valid roles: `admin`, `guru`, `siswa`, `trial`.

## MikroTik Integration

The app communicates with the router exclusively through `app/utils/mikrotik.py` (`MikroTikClient`, obtained via `get_mikrotik_client()`). There is no direct CLI or Winbox access from the UI.

### Router setup

On the router, create a dedicated API user:

```
/ip hotspot set [find default=yes] html-directory=flash/hotspot

/user group
add name=api-group policy=api

/user
add name=apiuser group=api-group password=apipassword
```

Then enter the connection details (host, port, user, password, SSL) on the **Settings** page and click **Test Connection**.

### Role–profile mapping

Roles map to MikroTik hotspot profiles via a `RoleProfile` table:

| Role | Default profile |
|---|---|
| `admin` | `admin` |
| `guru` | `guru` |
| `siswa` | `siswa` |
| `trial` | `trial` |

Mappings can be initialized with **Init Default Profiles** on the Settings page or edited manually. When a hotspot user is created, the app sets the router profile to the role name and stores the role in the user's `comment` field (`role:<role>`).

## Automated Synchronization

Background tasks run in a scheduler thread started by `run.py`:

| Task | Interval | Behavior |
|---|---|---|
| Student time control | every 5 min | When enabled in Settings, enables all `siswa` users during school hours (07:00–14:00 WITA) and disables + disconnects them outside those hours |
| Trial user expiry | every 60 min | Disables trial users whose `expires_at` has passed, marks them `expired` in the local DB, and writes an audit log entry |

The built-in scheduler runs automatically as part of `python run.py`. There are two standalone alternatives for running the expiry check outside the web process:

```bash
# Run the expiry check once and exit (cron-friendly)
python expire_users.py

# Run as a daemon with the same logic, every hour by default
python scheduler.py

# One-shot via scheduler, or with a custom interval (minutes)
python scheduler.py --once
python scheduler.py --interval 30
```

Failures are logged to stdout; the scheduler loop catches exceptions and continues to the next check.

## Database

- **Engine:** SQLite (`instance/eduhotspotportal.db` by default)
- **Creation:** `db.create_all()` runs automatically on application start; no migration management is currently used
- **Models:**
  - `operators` — portal users (login accounts, RBAC roles)
  - `hotspot_users` — locally cached hotspot users (status, MAC, expiration, timestamps)
  - `role_profiles` — role → MikroTik profile mapping
  - `audit_logs` — operator action history
  - `settings` — key/value application settings
- The router remains the source of truth for hotspot users; the local `hotspot_users` table is used for tracking (expiration, MAC binding, creation dates) and is synced from router data.

## Development

### Configuration

Configuration classes live in `config.py`:

- `DevelopmentConfig` — `DEBUG = True` (default)
- `ProductionConfig` — `DEBUG = False`

### Testing

There is currently no automated test suite. `test_mikrotik.py` is a standalone script that verifies reachability and API access to a router:

```bash
python test_mikrotik.py <host> <user> <password> [port]
```

## Deployment

The Flask development server is not suitable for production traffic. When deploying:

1. Run with `ProductionConfig` (or derive your own config object from `Config` and set `DEBUG = False`).
2. Run behind a production WSGI server (e.g., Gunicorn) and a reverse proxy.
3. Set a strong `SECRET_KEY` and a non-default admin password via `DEFAULT_ADMIN_PASSWORD` before first boot.
4. Serve over HTTPS and, for router security, restrict the MikroTik API user to the server's IP only.

## Security

- Portal accounts use hashed passwords (Werkzeug `generate_password_hash`); the default `admin` password must be changed after first login.
- MikroTik router credentials are stored in the app's `settings` table and entered through the admin-only Settings page — not hardcoded in source.
- All state-changing operations are recorded in `audit_logs` (operator, action, target, timestamp).
- **Known limitation (MVP):** hotspot user passwords are stored and returned in plaintext by the router API and are shown/exported in XLSX for operational needs. Use an HTTPS deployment and restrict access to the panel accordingly.

## Troubleshooting

### "Connection failed" when testing MikroTik settings

Check, in order:

1. The router has the API service enabled on the configured port (8728, or 8729 for SSL).
2. The API user exists and belongs to a group with the `api` policy.
3. Firewall rules allow the app's server to reach the router port.
4. Credentials and SSL toggle match the router configuration.

### The scheduler is not disabling/enabling students

Student time control only runs when the `Enable student time control` toggle is turned on in Settings. It also matches users by their MikroTik hotspot profile equal to `siswa`.

### Port 7171 is already in use

Change the port in the `app.run(...)` call in `run.py`, or run behind a reverse proxy that forwards to the app.

## Contributing

1. Fork the repository.
2. Create a feature branch: `git checkout -b feature/your-feature`.
3. Make your changes and test them locally.
4. Commit with a descriptive message.
5. Open a pull request.

## License

A license has not yet been specified.

## Roadmap

- Notifications via WhatsApp/email for user events
- Single sign-on (SSO) integration
- Integration with the school's academic information system
