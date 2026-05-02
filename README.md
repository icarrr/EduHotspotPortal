# EduHotspotPortal (EHP)

**Edu Hotspot Portal (EHP)** adalah aplikasi web berbasis admin panel untuk membantu operator sekolah dalam mengelola akun hotspot pada perangkat MikroTik tanpa perlu akses langsung ke Winbox atau CLI.

## 🎯 Fitur Utama (MVP - Phase 1)

- ✅ **Dashboard** - Ringkasan kondisi hotspot (total user, online, disabled, new today)
- ✅ **User Management (CRUD)** - Kelola akun hotspot via MikroTik API
- ✅ **Online Sessions Monitoring** - Lihat user yang sedang online + disconnect
- ✅ **Import XLSX** - Import user massal dari file Excel dengan auto-generate password
- ✅ **Reset Password** - Reset password 1 klik
- ✅ **Enable/Disable User** - Aktif/nonaktifkan akun
- ✅ **Search & Helpdesk Mode** - Cari user cepat, aksi cepat
- ✅ **Audit Log** - Lacak aktivitas operator
- ✅ **Role-Based Access Control (RBAC)** - Admin IT, Operator, Siswa
- ✅ **Role-Profile Mapping** - Mapping role ke profile MikroTik
- ✅ **Settings** - Konfigurasi koneksi MikroTik + test connection

## 🏗️ Tech Stack

- **Backend:** Flask 3.0.0 (Python)
- **Frontend:** AdminLTE 3.2.0 (Bootstrap-based admin template)
- **Database:** SQLite (simple, no MySQL required)
- **MikroTik API:** librouteros 3.2.1
- **Excel Support:** openpyxl 3.1.2

## 📋 Prasyarat

- Python 3.8+
- Virtual environment (venv)
- MikroTik router dengan API enabled (port 8728/8729)
- AdminLTE sudah terintegrasi di `app/static/adminlte/`

## 🚀 Instalasi

### 1. Clone Repository
```bash
git clone https://github.com/icarrr/EduHotspotPortal.git
cd EduHotspotPortal
```

### 2. Setup Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# atau
venv\Scripts\activate  # Windows
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Konfigurasi Environment
```bash
cp .env.example .env
```
Edit `.env` file:
```env
FLASK_APP=run.py
FLASK_ENV=development
SECRET_KEY=your-secret-key-here

# Database (SQLite - default sudah siap)
DB_PATH=instance/eduhotspotportal.db

# MikroTik
MIKROTIK_HOST=192.168.1.1
MIKROTIK_PORT=8728
MIKROTIK_USER=apiuser
MIKROTIK_PASSWORD=apipassword
MIKROTIK_USE_SSL=false
```

### 5. Initialize Database
```bash
python run.py
```
Aplikasi akan otomatis membuat:
- Database SQLite di `instance/eduhotspotportal.db`
- Default admin: `admin` / `admin123`

### 6. Jalankan Aplikasi
```bash
python run.py
```
Buka browser: `http://127.0.0.1:5000/auth/login`

## 🔐 Default Login

| Username | Password | Role |
|----------|----------|------|
| admin | admin123 | Admin IT |

**Peringatan:** Ganti password default setelah login pertama!

## 👥 Role & Akses

| Fitur | Admin IT | Operator | Siswa |
|-------|----------|----------|-------|
| Dashboard | ✅ | ✅ | ✅ |
| User Management | ✅ | ✅ | ❎ |
| Online Sessions | ✅ | ✅ | ❎ |
| Import XLSX | ✅ | ✅ | ❎ |
| Audit Logs | ✅ | ❎ | ❎ |
| Operators | ✅ | ❎ | ❎ |
| Settings | ✅ | ❎ | ❎ |

## 📊 Role-Profile Mapping

| Role | MikroTik Profile |
|------|-------------------|
| admin | `admin` |
| guru | `guru` |
| siswa | `siswa` |
| trial | `trial` |

Mapping dapat diatur di menu **Settings** → "Init Default Profiles" atau manual via "Add Mapping".

## 📥 Format Import XLSX

Download template: **User Management** → **Import** → **Download XLSX Template**

| username | nama | role |
|----------|------|------|
| 12345 | Budi Santoso | siswa |
| 67890 | Siti Nurhaliza | guru |
| 11111 | Admin User | admin |

**Note:**
- Password akan di-generate otomatis
- Password ditampilkan setelah import selesai
- Dupikat akan di-skip otomatis

## 🔧 API Connection (MikroTik)

1. Pastikan API diaktifkan di MikroTik:
   ```
   /ip hotspot
   set [ find default=yes ] html-directory=flash/hotspot
   
   /user group
   add name=api-group policy=api
   
   /user
   add name=apiuser group=api-group password=apipassword
   ```

2. Test koneksi di menu **Settings** → **Test Connection**

## 📂 Struktur Proyek

```
EduHotspotPortal/
├── app/
│   ├── __init__.py          # App factory, blueprint registration
│   ├── extensions.py        # SQLAlchemy, LoginManager
│   ├── decorators.py      # RBAC decorators
│   ├── models/
│   │   └── __init__.py    # Operator, HotspotUser, RoleProfile, AuditLog, Setting
│   ├── routes/
│   │   ├── auth.py        # Login/logout
│   │   ├── main.py        # Dashboard
│   │   ├── users.py       # User management, import, audit logs
│   │   └── settings.py    # MikroTik settings, role-profile mapping
│   ├── templates/
│   │   ├── layouts/base.html
│   │   ├── auth/login.html
│   │   ├── main/dashboard.html
│   │   ├── users/ (index, add, edit, import, import_results, online, audit_logs, operators)
│   │   ├── settings/index.html
│   │   └── errors/ (403, 404, 500)
│   ├── static/
│   │   ├── adminlte/      # AdminLTE 3.2.0 (124MB)
│   │   ├── css/custom.css
│   │   └── js/custom.js
│   └── utils/
│       └── mikrotik.py     # MikroTik API client (librouteros)
├── config.py                 # App configuration
├── requirements.txt         # Python dependencies
├── run.py                   # Entry point
├── .env.example             # Environment variables template
├── .gitignore
└── ehp-prd.md              # Product Requirements Document
```

## 🚧‍♂️ Development

### Mode Debug
```bash
export FLASK_ENV=development
python run.py
```
Aplikasi akan restart otomatis saat file Python berubah.

### Tambah Operator Baru
1. Login sebagai Admin IT
2. Go to **Operators** menu
3. Klik **Add Operator**
4. Isi username, password, role (admin_it/operator/siswa)

### Inisialisasi Role-Profile Mapping
1. Login → **Settings**
2. Klik **Init Default Profiles**
3. Atau tambah manual via **Add Mapping**

## 📋 Phase 2 (Roadmap)

Fitur berikutnya yang akan ditambah:
- 🔜 **Device Binding (MAC)** - Ikat user ke MAC address tertentu
- ⏰ **Auto Expire User** - Set expiration, auto-disable expired users
- 📧 **Notifications (WA/Email)** - Alert untuk event user

## 🤝 Kontribusi

1. Fork repository
2. Buat branch fitur: `git checkout -b feature/nama-fitur`
3. Commit: `git commit -m "Add some feature"`
4. Push: `git push origin feature/nama-fitur`
5. Buat Pull Request

## 📄 License

Proyek ini bersifat open-source. Silakan gunakan sesuai kebutuhan.

## 📞 Kontak

- GitHub: [@icarrr](https://github.com/icarrr)
- Issues: [GitHub Issues](https://github.com/icarrr/EduHotspotPortal/issues)

---

**EduHotspotPortal** - Layer abstraction di atas MikroTik 🚀
