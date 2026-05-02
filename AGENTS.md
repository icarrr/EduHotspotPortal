# AGENTS.md - AI Agent Guidelines for EduHotspotPortal

## Repository Structure (Inferred)

```
EduHotspotPortal/
├── app/
│   ├── __init__.py              # Flask app factory, blueprint registration
│   ├── extensions.py              # SQLAlchemy, LoginManager initialization
│   ├── decorators.py            # RBAC decorators (admin_required, operator_required)
│   ├── models/
│   │   └── __init__.py        # Operator, HotspotUser, RoleProfile, AuditLog, Setting
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth.py            # Login/logout (CRITICAL: Auth)
│   │   ├── main.py            # Dashboard
│   │   ├── users.py           # User CRUD (CRITICAL: State mutation + MikroTik API)
│   │   └── settings.py        # MikroTik config (CRITICAL: External API credentials)
│   ├── templates/               # Jinja2 templates (AdminLTE-based)
│   ├── static/
│   │   ├── adminlte/          # AdminLTE 3.2.0 (124MB - in .gitignore)
│   │   ├── css/custom.css
│   │   └── js/custom.js
│   └── utils/
│       └── mikrotik.py         # MikroTik API client (CRITICAL: External API)
├── config.py                       # App configuration (CRITICAL: Secret keys)
├── requirements.txt                 # Python dependencies
├── run.py                         # Entry point
├── instance/                      # SQLite DB (in .gitignore)
├── .env                           # Environment variables (in .gitignore)
└── ehp-prd.md                    # Product Requirements Document
```

---

## 🚨 CRITICAL RISK AREAS - STRICT SAFEGUARDS REQUIRED

### 1. AUTHENTICATION & SESSION MANAGEMENT

**Risk:** Unauthorized access, session hijacking, brute force attacks

**STRICT RULES:**
- ✅ **NEVER** commit `.env` file or any file containing `SECRET_KEY`
- ✅ **ALWAYS** use `@login_required` on EVERY route except `/auth/login`
- ✅ **ALWAYS** use RBAC decorators (`@admin_required`, `@operator_required`) on routes based on PRD section 4:
  - Admin IT: Full access
  - Operator: User management only
  - Siswa: Dashboard only (read-only)
- ✅ **NEVER** allow user role modification via request parameters
- ✅ **ALWAYS** validate `current_user.is_active` before granting access
- ✅ **NEVER** log passwords in audit logs (log "Password reset" not the actual password in production)
- ✅ **MUST** implement rate limiting on `/auth/login` (max 5 attempts per IP per 15 minutes)
- ✅ **MUST** regenerate session ID on login (Flask-Login does this by default)
- ✅ **NEVER** store passwords in plaintext - ALWAYS use `generate_password_hash()` from werkzeug

**Code Pattern - ALL routes MUST follow:**
```python
@bp.route('/sensitive-action')
@login_required
@admin_required  # or @operator_required based on role
def sensitive_action():
    # Validate current_user.is_active
    if not current_user.is_active:
        abort(403)
    # Proceed with action
```

---

### 2. MIKROTIK API COMMUNICATIONS (External API)

**Risk:** Unauthorized router access, credential leakage, API injection, connection exhaustion

**STRICT RULES:**
- ✅ **NEVER** hardcode MikroTik credentials in source code
- ✅ **ALWAYS** store credentials in `Setting` table with proper access control
- ✅ **ALWAYS** use `get_mikrotik_client()` factory function (never create `MikroTikClient` directly)
- ✅ **ALWAYS** call `mikrotik.connect()` before any API operation
- ✅ **ALWAYS** call `mikrotik.disconnect()` after API operations (use try/finally)
- ✅ **NEVER** trust MikroTik API responses without validation
- ✅ **ALWAYS** wrap API calls in try/except for `LibRouterosError` and `ConnectionClosed`
- ✅ **NEVER** expose MikroTik API errors to end users (log them, show generic error)
- ✅ **MUST** validate all parameters before sending to MikroTik API
- ✅ **MUST** use SSL (port 8729) for production deployments

**Code Pattern - ALL MikroTik API calls MUST follow:**
```python
def mikrotik_operation(username, **kwargs):
    mikrotik = get_mikrotik_client()

    # Validate inputs STRICTLY
    if not username or not isinstance(username, str):
        return False, "Invalid username"

    # Sanitize inputs - no special characters that could be used for injection
    if any(char in '@:/?<>' for char in username):
        return False, "Invalid characters in username"

    try:
        if not mikrotik.connect():
            current_app.logger.error(f"MikroTik connection failed for {current_user.username}")
            return False, "Connection failed"

        # Perform operation
        success, message = mikrotik.some_operation(username, **kwargs)
        return success, message

    except (LibRouterosError, ConnectionClosed) as e:
        current_app.logger.error(f"MikroTik API error: {str(e)}")
        return False, "Operation failed"
    finally:
        mikrotik.disconnect()
```

---

### 3. STATE MUTATION (Database & MikroTik)

**Risk:** Data corruption, race conditions, inconsistent state between SQLite and MikroTik

**STRICT RULES:**
- ✅ **ALWAYS** use database transactions (`db.session.commit()`) after state changes
- ✅ **ALWAYS** log state mutations to `AuditLog` BEFORE committing
- ✅ **NEVER** perform MikroTik API operations and database operations in the same transaction without proper error handling
- ✅ **ALWAYS** validate data consistency between local DB and MikroTik after batch operations
- ✅ **MUST** use `db.session.rollback()` on errors
- ✅ **NEVER** delete users from MikroTik without logging the action first
- ✅ **ALWAYS** verify MikroTik operation success before updating local DB

**Code Pattern - State mutations MUST follow:**
```python
def create_user(username, password, role):
    # 1. Validate inputs
    if not username or not password:
        return False, "Missing required fields"

    # 2. Check for duplicates in BOTH MikroTik and local DB
    existing = HotspotUser.query.filter_by(username=username).first()
    if existing:
        return False, "User already exists"

    try:
        # 3. Perform MikroTik operation FIRST
        mikrotik = get_mikrotik_client()
        success, message = mikrotik.add_hotspot_user(username, password, role=role)

        if not success:
            return False, message

        # 4. Log to audit BEFORE committing
        log = AuditLog(
            operator_id=current_user.id,
            action='create',
            target_user=username,
            details=f"Role: {role}, Password: {password}"  # WARNING: Log password only for MVP, remove in prod
        )
        db.session.add(log)

        # 5. Update local DB to match MikroTik state
        user = HotspotUser(username=username, role=role, status='active')
        db.session.add(user)

        # 6. Commit ALL changes together
        db.session.commit()

        return True, "User created successfully"

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"User creation failed: {str(e)}")
        return False, "Creation failed"
```

---

### 4. FILE UPLOAD (XLSX Import)

**Risk:** Malicious files, DoS via large files, path traversal, macro injection

**STRICT RULES:**
- ✅ **ALWAYS** validate file extension (`.xlsx` only)
- ✅ **MUST** limit file size (max 5MB)
- ✅ **ALWAYS** use `openpyxl.load_workbook()` with `data_only=True` to prevent formula injection
- ✅ **NEVER** trust cell values without type checking
- ✅ **ALWAYS** validate row count (max 1000 rows per import)
- ✅ **MUST** sanitize all string values (strip, check length)
- ✅ **NEVER** use `eval()` or `exec()` on imported data
- ✅ **ALWAYS** wrap `load_workbook()` in try/except

**Code Pattern - File uploads MUST follow:**
```python
ALLOWED_EXTENSIONS = {'.xlsx'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
MAX_ROWS = 1000

@bp.route('/import', methods=['POST'])
@login_required
@operator_required
def import_users():
    if 'xlsx_file' not in request.files:
        flash('No file uploaded', 'danger')
        return redirect(url_for('users.import_users'))

    file = request.files['xlsx_file']

    # Validate file presence
    if file.filename == '':
        flash('No file selected', 'danger')
        return redirect(url_for('users.import_users'))

    # Validate extension
    if not file.filename.endswith(tuple(ALLOWED_EXTENSIONS)):
        flash('Please upload an XLSX file', 'danger')
        return redirect(url_for('users.import_users'))

    # Validate file size
    file.seek(0, 2)  # Seek to end
    size = file.tell()
    file.seek(0)  # Reset
    if size > MAX_FILE_SIZE:
        flash('File too large (max 5MB)', 'danger')
        return redirect(url_for('users.import_users'))

    try:
        wb = openpyxl.load_workbook(file.stream, data_only=True)
        ws = wb.active

        rows = list(ws.iter_rows(min_row=2, values_only=True))
        if len(rows) > MAX_ROWS:
            flash(f'Too many rows (max {MAX_ROWS})', 'danger')
            return redirect(url_for('users.import_users'))

        # Process rows with strict validation
        for idx, row in enumerate(rows, start=2):
            if not row or not row[0]:
                continue

            # Validate each cell strictly
            username = str(row[0]).strip() if row[0] else ''
            if len(username) < 3 or len(username) > 50:
                errors.append(f'Row {idx}: Username must be 3-50 characters')
                continue

            # Sanitize username - only allow alphanumeric and underscore
            if not username.replace('_', '').isalnum():
                errors.append(f'Row {idx}: Username can only contain letters, numbers, underscore')
                continue

            # ... rest of processing

    except Exception as e:
        current_app.logger.error(f"XLSX import error: {str(e)}")
        flash('Error processing file', 'danger')
        return redirect(url_for('users.import_users'))
```

---

### 5. INPUT VALIDATION (All User Inputs)

**Risk:** XSS, SQL injection (though SQLAlchemy ORM helps), command injection

**STRICT RULES:**
- ✅ **ALWAYS** validate `request.form` and `request.args` values
- ✅ **ALWAYS** use Flask's `escape()` or Markup for user-generated content in templates
- ✅ **NEVER** use `safe` filter in Jinja2 templates for user content
- ✅ **ALWAYS** limit string lengths (username: 3-50, name: 1-100, role: must be in whitelist)
- ✅ **MUST** use whitelist validation for roles: `['admin', 'guru', 'siswa', 'trial']`
- ✅ **NEVER** use string formatting (f-strings) with user input in database queries

**Allowed roles (WHITELIST):**
```python
ALLOWED_ROLES = {'admin', 'guru', 'siswa', 'trial'}

def validate_role(role):
    if role not in ALLOWED_ROLES:
        return 'siswa'  # Default safe role
    return role
```

---

### 6. ERROR HANDLING & INFORMATION LEAKAGE

**Risk:** Revealing stack traces, internal paths, database structure to attackers

**STRICT RULES:**
- ✅ **NEVER** show Python tracebacks to end users in production
- ✅ **ALWAYS** use custom error pages (403.html, 404.html, 500.html are in `app/templates/errors/`)
- ✅ **NEVER** log sensitive data (passwords, API keys) - use `current_app.logger` not `print()`
- ✅ **ALWAYS** return generic error messages to users ("Operation failed" not "Connection refused by 192.168.1.1:8728")
- ✅ **MUST** configure Flask's `PROPAGATE_EXCEPTIONS = False` in production

---

### 7. AUDIT LOGGING (Non-Negotiable)

**Risk:** No accountability, compliance violations

**STRICT RULES:**
- ✅ **MUST** log ALL state-changing operations to `AuditLog`:
  - User create/update/delete
  - Password reset
  - Settings changes
  - Role-profile mapping changes
- ✅ **ALWAYS** include: `operator_id`, `action`, `target_user`, `timestamp`
- ✅ **NEVER** skip audit logging for "minor" changes
- ✅ **MUST** log from `current_user.id` (not trusted input)

**Required audit actions (whitelist):**
```python
AUDIT_ACTIONS = {
    'create', 'update', 'delete', 'reset', 'enable', 'disable',
    'bulk_import', 'settings_update', 'profile_mapping_change'
}
```

---

### 8. DEPLOYMENT SECURITY

**Risk:** Debug mode in production, weak secrets, unprotected admin panel

**STRICT RULES:**
- ✅ **NEVER** run with `debug=True` in production
- ✅ **ALWAYS** generate a strong `SECRET_KEY` (min 32 bytes random)
- ✅ **MUST** use environment variables for all secrets (never commit `.env`)
- ✅ **MUST** restrict MikroTik API access to server IP only (per PRD section 8)
- ✅ **ALWAYS** use HTTPS in production (SSL/TLS)
- ✅ **MUST** set `SESSION_COOKIE_SECURE = True` and `REMEMBER_COOKIE_SECURE = True`

---

## 🛡️ CODE REVIEW CHECKLIST (Mandatory)

Before ANY commit, verify:

- [ ] All routes have `@login_required` (except login/logout)
- [ ] All routes have appropriate RBAC decorator
- [ ] All MikroTik API calls use `get_mikrotik_client()` factory
- [ ] All state mutations are logged to `AuditLog`
- [ ] All user inputs are validated against whitelists
- [ ] No credentials in source code
- [ ] No `.env` or `instance/` in git tracking
- [ ] All errors are caught and logged (no tracebacks to users)
- [ ] File uploads have extension, size, and content validation
- [ ] Database transactions use proper commit/rollback
- [ ] `adminlte/` directory is in `.gitignore`

---

## 🚫 WHAT NOT TO DO (Anti-Patterns)

❌ **NEVER** create routes without authentication
❌ **NEVER** trust MikroTik API responses without validation
❌ **NEVER** use `eval()`, `exec()`, or `pickle` with user data
❌ **NEVER** log passwords in production audit logs
❌ **NEVER** skip `db.session.rollback()` on errors
❌ **NEVER** commit `.env`, `*.db`, or `adminlte/` files
❌ **NEVER** use string formatting for database queries
❌ **NEVER** show detailed error messages to end users

---

## 📋 TESTING REQUIREMENTS (Before Phase 2)

**MANDATORY tests before proceeding to Phase 2:**

1. **Authentication tests:**
   - Login with valid/invalid credentials
   - Access restricted routes without login (expect 302/401)
   - Access admin routes as operator (expect 403)

2. **MikroTik API tests:**
   - Test connection with invalid credentials
   - Test API operations with invalid parameters
   - Verify connection cleanup (disconnect called)

3. **File upload tests:**
   - Upload non-XLSX file (expect error)
   - Upload file >5MB (expect error)
   - Upload XLSX with malicious formulas (expect safe handling)

4. **RBAC tests:**
   - Verify each role can only access allowed routes
   - Verify `has_role()` method works correctly

---

## 🚨 WHEN IN DOUBT

**STOP and ASK** if:
- You're unsure about authentication requirements for a new route
- You're adding new external API calls
- You're handling file uploads differently
- You're modifying the `Operator` or `AuditLog` models
- You see credentials or secrets in code

**Over-constrain rather than under-specify.**

---

**Last updated:** 2026-05-02  
**Enforced by:** All AI agents working on this repository
