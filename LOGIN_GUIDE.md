# Login & Authentication Guide

## 🔐 Fitur Login/Logout

Login dan logout system sudah fully integrated dengan RBAC!

## 📝 Setup Login

### 1. Pastikan Superuser Sudah Ada
```bash
py manage.py createsuperuser
```
Isi username, email, dan password. User ini akan otomatis menjadi Admin.

### 2. Setup Groups (Jika Belum)
```bash
py manage.py setup_groups
```

### 3. Run Server
```bash
py manage.py runserver
```

## 🚀 Cara Pakai

### Login
1. Buka http://localhost:8000/operasional/login/
2. Masukkan username & password
3. Centang "Ingat saya di perangkat ini" (optional) untuk session 2 minggu
4. Klik **Login**

### Logout
1. Lihat navbar atas (sebelah kanan)
2. Ada info user + role
3. Klik tombol **Logout** (merah)

## 📋 Login Behavior

| Role | Login | Redirect To | Access |
|------|-------|-------------|--------|
| Admin | ✅ | Dashboard | Semua halaman |
| Supervisor | ✅ | Dashboard | Analytics, Lunasi Order |
| Teknisi | ✅ | Dashboard | Dashboard, Detail Order, Cetak Struk |
| Customer | ✅ | Dashboard | Dashboard (filtered) |

## 🔒 Protected Views

### Tanpa Login
- Redirect ke `/operasional/login/` untuk semua protected routes

### Dengan Role Restriction
- **Admin Only**: `/tambah/` (create order), `/customer/new/`
- **Supervisor Only**: `/analytics/`, `/api/analytics/data/`, lunasi order
- **Login Required**: `/` (dashboard), `/order/<id>/`, `/order/<id>/print/`

## 💾 Session Management

| Setting | Value | Notes |
|---------|-------|-------|
| Default Duration | 2 weeks | Berlaku jika "Ingat saya" dicentang |
| Without Remember | Browser close | Session hilang saat browser ditutup |
| Session Cookie | HTTPOnly | Aman dari XSS attack |
| Secure Mode | Development | Set ke True di production (HTTPS) |

## 🎨 UI Changes

### Before Login
```
[Logo] SOLECLEAN          [Login Button]
```

### After Login
```
[Logo] SOLECLEAN  Dashboard  Keuangan  +Terima Order  [User Info] [Logout]
```

User info menampilkan:
- Username
- Role (dari group)

## 📱 Responsive Design

Login form responsive di semua ukuran layar:
- ✅ Mobile (320px+)
- ✅ Tablet (768px+)
- ✅ Desktop (1024px+)

## 🧪 Test Cases

### Test Login Success
1. Buka `/operasional/login/`
2. Masukkan username & password admin
3. ✅ Redirect ke dashboard dengan welcome message

### Test Logout
1. Click logout button di navbar
2. ✅ Redirect ke login page dengan goodbye message

### Test Role Restriction (Teknisi trying to access Analytics)
1. Login sebagai Teknisi
2. Coba akses `/operasional/analytics/`
3. ✅ Redirect ke dashboard (access denied)

### Test Session Expiry (without Remember)
1. Login tanpa centang "Ingat saya"
2. Tutup browser
3. Buka browser lagi
4. ✅ Session expired, harus login lagi

## ⚙️ Configuration (settings.py)

```python
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'dashboard'
LOGOUT_REDIRECT_URL = 'login'
SESSION_COOKIE_AGE = 1209600  # 2 weeks
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
SESSION_COOKIE_HTTPONLY = True
```

## 🔑 User Management via Admin

1. Buka /admin/auth/user/
2. Pilih atau create user baru
3. Scroll ke RBAC Groups section
4. Assign ke group (Admin/Supervisor/Teknisi/Customer)
5. Save

## 🚨 Troubleshooting

### Error: "Username dan password tidak cocok"
- Pastikan username & password benar
- Pastikan user sudah dibuat di admin
- Pastikan user sudah di-assign ke group

### Error: "Anda tidak memiliki akses ke halaman ini"
- User belum di-assign ke group yang tepat
- Buka /admin/auth/user/ → assign ke group
- Logout & login ulang

### Session tidak disimpan
- Centang "Ingat saya" di login form
- Atau extend SESSION_COOKIE_AGE di settings

## 📚 Related Files

- [operasional/views.py](operasional/views.py) - `user_login()`, `user_logout()`
- [operasional/templates/login.html](operasional/templates/login.html) - Login form UI
- [operasional/templates/base.html](operasional/templates/base.html) - Navbar dengan user info & logout
- [config/settings.py](config/settings.py) - Authentication settings
- [operasional/urls.py](operasional/urls.py) - login, logout routes

---

Login system siap digunakan! 🎉
