# RBAC (Role-Based Access Control) Setup Guide

Sistem RBAC sudah diimplementasikan! Ikuti langkah-langkah berikut untuk setup:

## 📋 Langkah Setup

### 1. Jalankan Management Command (Setup Groups)
```bash
python manage.py setup_groups
```
Command ini akan membuat 4 groups otomatis:
- **Admin** - Full access ke semua fitur
- **Teknisi** - Update order status, manage expenses
- **Supervisor** - View analytics, manage finances, reports
- **Customer** - View own orders (restricted in views)

### 2. Buat Superuser (jika belum ada)
```bash
python manage.py createsuperuser
```

### 3. Login ke Admin Dashboard
Buka: http://localhost:8000/admin/

### 4. Assign Users to Groups
1. Klik **Users** di admin panel
2. Pilih atau buat user baru
3. Scroll ke bawah, lihat section **RBAC Groups**
4. Pilih group yang sesuai (Admin/Teknisi/Supervisor/Customer)
5. Save

## 🔐 Permission Overview

### Admin
- ✅ Full access ke semua views
- ✅ Create/edit/delete orders, customers, services
- ✅ Create/edit/delete expenses
- ✅ View analytics & reports
- ✅ Manage users & groups

### Supervisor
- ✅ View analytics & financial reports
- ✅ Create/edit/delete expenses
- ✅ View orders (read-only, can't create new)
- ✅ Process payments (lunasi_order)
- ❌ Cannot create orders
- ❌ Cannot create customers

### Teknisi
- ✅ View dashboard with pending orders
- ✅ Update order item status (PENDING → PROCESS → READY)
- ✅ Create/edit expenses
- ✅ Print struk (receipts)
- ❌ Cannot access analytics
- ❌ Cannot create orders
- ❌ Cannot create customers

### Customer
- ✅ View own orders (jika diimplementasikan)
- ❌ Cannot access analytics
- ❌ Cannot view order prices
- ❌ Cannot manage expenses

## 🔗 Protected Views

| View | Min. Role | Decorators |
|------|-----------|-----------|
| dashboard | None (login required) | @login_required |
| analytics | Supervisor | @login_required + @user_passes_test(is_supervisor) |
| api_analytics_data | Supervisor | @login_required + @user_passes_test(is_supervisor) |
| tambah_order | Admin | @login_required + @user_passes_test(is_admin) |
| tambah_customer | Admin | @login_required + @user_passes_test(is_admin) |
| detail_order | Teknisi | @login_required |
| cetak_struk | Teknisi | @login_required |
| lunasi_order | Supervisor | @login_required + @user_passes_test(is_supervisor) |

## 📝 Test Cases

### Test sebagai Admin:
1. ✅ Bisa akses semua halaman
2. ✅ Bisa create order & customer
3. ✅ Bisa view analytics
4. ✅ Bisa manage expenses

### Test sebagai Supervisor:
1. ✅ Bisa akses analytics
2. ✅ Bisa manage expenses
3. ✅ Bisa lunasi order
4. ❌ Redirect ke dashboard jika akses /tambah/ (create order)

### Test sebagai Teknisi:
1. ✅ Bisa view dashboard
2. ✅ Bisa update order status
3. ✅ Bisa create expenses
4. ✅ Bisa cetak struk
5. ❌ Redirect jika akses /analytics/

### Test Tanpa Login:
1. ❌ Redirect ke login page untuk semua protected views

## 🛠️ Helper Functions (di views.py)

```python
is_admin(user)          # Check if user in 'Admin' group
is_supervisor(user)     # Check if user in 'Supervisor' or 'Admin' group
is_teknisi(user)        # Check if user in 'Teknisi' or 'Admin' group
```

## 🎨 Template Conditionals (optional, untuk UI)

Jika ingin conditionally show/hide elements di templates:

```html
{% if user.groups.all|length > 0 %}
  <p>User role: {{ user.groups.all|first }}</p>
{% endif %}

<!-- Show delete button only for Admin -->
{% if user.groups.all|first.name == "Admin" %}
  <button class="btn btn-danger">Hapus Order</button>
{% endif %}
```

## ⚠️ Important Notes

- **Auto-grant Admin status**: Users dengan `is_staff=True` automatically dianggap Admin
- **Login required**: Semua views (kecuali login/signup) memerlukan login
- **Default redirect**: User tanpa permission di-redirect ke dashboard
- **Superuser bypass**: Django superusers bypass semua permission checks

## 🚀 Next Steps (Opsional)

1. **Tambah template conditionals** - Conditional show/hide menu items berdasarkan role
2. **Tambah audit logging** - Track siapa yang modify data
3. **Tambah password policies** - Force strong passwords untuk Supervisor/Admin
4. **Customize 403/404 pages** - Friendly error pages untuk access denied

---

Setup selesai! 🎉
