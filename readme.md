# 👟 SoleClean Management System

![Django](https://img.shields.io/badge/Django-5.0-green?style=for-the-badge&logo=django)
![TailwindCSS](https://img.shields.io/badge/Tailwind_CSS-3.4-blue?style=for-the-badge&logo=tailwind-css)
![Status](https://img.shields.io/badge/Status-Active-success?style=for-the-badge)

Aplikasi manajemen operasional (POS) dan CRM khusus untuk bisnis **Laundry Sepatu**, dibangun dengan **Django Framework**. Aplikasi ini dirancang untuk memisahkan alur kerja teknisi (Operasional) dan pemilik bisnis (Keuangan/Analytics).

## 🔥 Fitur Unggulan

### 1. 🛠 Dashboard Operasional (Untuk Teknisi)
- **Antrian Real-time:** Memantau status sepatu (Process, Ready, Completed).
- **Strict Input Order:** Sistem input order menggunakan dropdown pelanggan yang tervalidasi (mencegah typo data).
- **WhatsApp Integration:** Tombol "One-Click" untuk mengirim notifikasi sepatu selesai ke pelanggan dengan template pesan otomatis.

### 2. 📊 Dashboard Analytics (Untuk Owner)
- **Cash Basis Accounting:** Pendapatan hanya dihitung ketika status order "Completed" (Sudah diambil & Lunas).
- **Financial Summary:** Laporan omzet harian, bulanan, dan performa jumlah cuci sepatu secara real-time.
- **Separate View:** Halaman analytics terpisah dari dashboard kerja agar teknisi fokus pada operasional.

### 3. 👥 Customer Relationship Management (CRM)
- **Database Pelanggan:** Penyimpanan data pelanggan terpusat.
- **Auto-Fill Data:** Saat memilih pelanggan lama, data WhatsApp dan Alamat otomatis terisi.

### 4. 🎨 Modern UI/UX
- **Responsive Design:** Tampilan optimal di Desktop (Laptop Admin) maupun Mobile (iPhone/Android).
- **Tailwind CSS:** Desain antarmuka yang bersih, modern, dan user-friendly.

---

## 🚀 Cara Instalasi (Local Development)

Ikuti langkah ini untuk menjalankan proyek di komputer lokal Anda:

### 1. Clone Repository
```bash
git clone [https://github.com/username-anda/soleclean-app.git](https://github.com/VonMatilda07/soleclean-app.git)
cd soleclean-app

2. Buat Virtual Environment
# Windows
python -m venv env
env\Scripts\activate

# Mac/Linux
python3 -m venv env
source env/bin/activate

3. Install Depedencies
pip install django django-cleanup pillow

4. Setup Database & Static Files
python manage.py makemigrations
python manage.py migrate
python manage.py collectstatic

5.Create Superuser ( Admin )
python manage.py createsuperuser
# Ikuti instruksi di layar (masukkan username & password)

6. Jalankan Server
python manage.py runserver

📂 Struktur Proyek
soleclean-app/
├── config/             # Konfigurasi utama Django
├── operasional/        # Aplikasi inti (Views, Models, Forms)
│   ├── migrations/     # File migrasi database
│   ├── static/         # File statis lokal aplikasi
│   └── templates/      # File HTML (Frontend)
├── static/             # Static root (Logo, CSS, JS global)
├── media/              # Upload user (Foto sepatu sebelum/sesudah)
├── db.sqlite3          # Database lokal
└── manage.py           # Command line utility
```
---
👨‍💻 Author
Muhammad Athfal Aulia Putra, S.Kom

Owner of SoleClean & Mahakam Coffee Roastery

Fullstack Developer (Django, React, Laravel)
---
📄 License
This project is licensed under the MIT License.
