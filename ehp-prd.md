# Product Requirements Document (PRD)

## **Edu Hotspot Portal (EHP)**

---

## 1. 🎯 Overview

**Edu Hotspot Portal (EHP)** adalah aplikasi web berbasis admin panel untuk membantu operator sekolah dalam mengelola akun hotspot pada perangkat MikroTik tanpa perlu akses langsung ke Winbox atau CLI.

Sistem ini dirancang untuk:

- Menyederhanakan manajemen user hotspot
- Mengurangi risiko kesalahan konfigurasi router
- Memberikan akses terbatas kepada operator non-teknis

---

## 2. 🧩 Problem Statement

### Masalah saat ini:

- Operator harus login ke MikroTik (Winbox/WebFig)
- Risiko salah konfigurasi router cukup tinggi
- Tidak ada sistem audit perubahan user
- Proses tambah/reset user masih manual
- Tidak ada integrasi dengan data siswa

---

## 3. 🎯 Objectives

### Tujuan utama:

- Membuat **interface sederhana** untuk kelola user hotspot
- Mengurangi ketergantungan pada akses langsung ke router
- Mendukung pengelolaan massal user (bulk)
- Menyediakan monitoring sederhana user hotspot

---

## 4. 👥 User Personas

### 1. Admin IT

- Setup awal sistem
- Konfigurasi koneksi ke MikroTik
- Monitoring global

### 2. Operator Sekolah (TU / Lab)

- Tambah/edit user
- Reset password
- Aktivasi/nonaktif akun
- Import data siswa

### 3. Kepala Sekolah (Opsional)

- Hanya melihat laporan

---

## 5. 🚀 Features

---

## 5.1 Dashboard

### Deskripsi:

Menampilkan ringkasan kondisi hotspot.

### Komponen:

- Total user
- User aktif (online)
- User nonaktif
- User baru hari ini
- Top user bandwidth (opsional)

---

## 5.2 User Management

### Deskripsi:

CRUD akun hotspot

### Fitur:

- Tambah user
- Edit user
- Reset password
- Enable / Disable user
- Hapus user
- Force logout user aktif

### Field:

```
username
password
role (siswa/guru/staff)
profile (mapping MikroTik)
status (active/disabled)
created_at
```

---

## 5.3 Role & Profile Mapping

### Deskripsi:

Mapping role ke profile hotspot di MikroTik

### Contoh:

| Role | Profile MikroTik |
| --- | --- |
| Siswa | hotspot-siswa |
| Guru | hotspot-guru |
| Staff | hotspot-staff |

---

## 5.4 Online Session Monitoring

### Deskripsi:

Menampilkan user yang sedang online

### Data:

- username
- IP address
- MAC address
- login time
- usage duration

### Aksi:

- Disconnect user

---

## 5.5 Import Data (Bulk User)

### Deskripsi:

Import user dari file CSV/Excel

### Format:

```
username,nama,role
12345,Budi,siswa
67890,Siti,guru
```

### Fitur:

- Validasi data
- Skip duplicate
- Auto-generate password

---

## 5.6 Search & Helpdesk Mode

### Deskripsi:

Mempermudah operator menangani masalah user

### Fitur:

- Search cepat (nama / username)
- Reset password 1 klik
- Enable/disable cepat
- Lihat status user

---

## 5.7 Audit Log

### Deskripsi:

Mencatat aktivitas operator

### Data:

- operator
- aksi (create/update/delete/reset)
- target user
- timestamp

---

## 5.8 Settings

### Fitur:

- Koneksi ke MikroTik (IP, port, user API)
- Default password policy
- Default role mapping

---

## 6. 🏗️ System Architecture

```
Operator (Browser)
        ↓
Web Application (Hosting/VPS)
        ↓ API
MikroTik Router
        ↓
Hotspot Users
```

### Komunikasi:

- MikroTik API (port 8728 / 8729 SSL)

---

## 7. ⚙️ Technical Requirements

### Backend:

- PHP (Laravel) / Python (Flask)
- MikroTik API Client

### Frontend:

- Bootstrap / AdminLTE

### Database:

- MySQL / MariaDB

### Deployment:

- Shared hosting / VPS kecil

---

## 8. 🔐 Security Requirements

- Gunakan API user khusus (bukan admin)
- Batasi akses API hanya dari IP server
- Gunakan API SSL (8729)
- Authentication login panel (session-based)
- Role-based access control (RBAC)

---

## 9. 📊 Non-Functional Requirements

| Aspect | Requirement |
| --- | --- |
| Performance | <1s response untuk operasi user |
| Availability | 99% uptime |
| Usability | Mudah digunakan operator non-IT |
| Scalability | Support ≥ 2000 user |

---

## 10. 🧪 MVP Scope (Versi 1)

Fokus awal:

- Dashboard
- User Management (CRUD)
- Online Users
- Import CSV
- Reset password
- Enable/Disable user

**Tidak termasuk dulu:**

- Integrasi SSO
- Advanced analytics
- Mobile app

---

## 11. 🗺️ Roadmap

### Phase 1 (MVP)

- Core user management
- Monitoring
- Import data

### Phase 2

- Device binding (MAC)
- Auto expire user
- Notifikasi WA/email

### Phase 3

- Integrasi sistem akademik
- SSO login
- Captive portal custom

---

## 12. 💡 Future Enhancements

- Login hotspot pakai email sekolah
- Integrasi Google Workspace
- Statistik penggunaan internet siswa
- Filtering berdasarkan kelas/jurusan
- API untuk integrasi eksternal

---

## 13. 📌 Success Metrics

- Waktu create user ↓ >80%
- Operator tidak perlu akses Winbox
- Jumlah kesalahan konfigurasi ↓
- Kepuasan operator meningkat

---

## 14. 🧠 Kesimpulan

Produk ini bukan sekadar tool, tapi:

👉 **Layer abstraction di atas MikroTik**

👉 Membuat sistem lebih aman, terstruktur, dan scalable