from django.db import models
from django.utils import timezone
from PIL import Image   # <-- Library Pengolah Gambar
from io import BytesIO  # <-- Buat nyimpen file sementara
from django.core.files.uploadedfile import InMemoryUploadedFile
import sys

# ==========================================
# 1. TABEL PELANGGAN (CRM)
# ==========================================
class Customer(models.Model):
    nama = models.CharField(max_length=100)
    whatsapp = models.CharField(max_length=15, unique=True)
    alamat = models.TextField(blank=True, null=True)
    join_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nama} ({self.whatsapp})"

# ==========================================
# 2. TABEL SERVICE
# ==========================================
class Service(models.Model):
    nama = models.CharField(max_length=100)
    harga = models.DecimalField(max_digits=10, decimal_places=0)
    durasi_hari = models.IntegerField(default=3)
    
    def __str__(self):
        return f"{self.nama} - Rp {self.harga}"

# ==========================================
# 3. TABEL ORDER (Update: Payment & Logic)
# ==========================================
class Order(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Baru Masuk'),
        ('PROCESS', 'Sedang Dikerjakan'),
        ('READY', 'Selesai / Siap Ambil'),
        ('COMPLETED', 'Sudah Diambil'),
    ]

    PAYMENT_CHOICES = [
        ('CASH', 'Cash / Tunai'),
        ('TRANSFER', 'Transfer Bank / QRIS'),
        ('UNPAID', 'Belum Bayar (Hutang)'),
    ]

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='orders')
    
    # Kolom Baru: Metode Pembayaran
    metode_pembayaran = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default='CASH')
    
    tanggal_masuk = models.DateTimeField(default=timezone.now)
    tanggal_selesai = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')

    def __str__(self):
        return f"Order #{self.id} - {self.customer.nama}"

    # STATUS TERTINGGI DARI ITEMS (Priority-based)
    @property
    def highest_item_status(self):
        """
        Return status dengan priority tertinggi dari semua items.
        Priority: PENDING > PROCESS > READY > COMPLETED
        """
        if not self.items.exists():
            return 'PENDING'
        
        status_priority = {
            'PENDING': 1,
            'PROCESS': 2,
            'READY': 3,
            'COMPLETED': 4,
        }
        
        # Ambil semua status items
        items_statuses = self.items.values_list('status', flat=True)
        
        # Return status dengan priority terendah (tertinggi prioritas = tertua)
        highest_status = min(items_statuses, key=lambda s: status_priority.get(s, 999))
        return highest_status

    @property
    def item_status_display(self):
        """Return display text untuk highest status"""
        status_map = {
            'PENDING': '🔴 Baru Masuk',
            'PROCESS': '🟡 Sedang Dikerjakan',
            'READY': '🔵 Siap Ambil',
            'COMPLETED': '✅ Sudah Diambil',
        }
        return status_map.get(self.highest_item_status, 'Baru Masuk')

    # LOGIKA DEADLINE / LAMPU MERAH
    @property
    def is_overdue(self):
        if self.items.exists():
            durasi = self.items.first().service.durasi_hari
            target = self.tanggal_masuk + timezone.timedelta(days=durasi)
            if timezone.now() > target and self.status not in ['READY', 'COMPLETED']:
                return True
        return False

    @property
    def deadline_info(self):
        if self.items.exists():
            durasi = self.items.first().service.durasi_hari
            target = self.tanggal_masuk + timezone.timedelta(days=durasi)
            sisa_waktu = target - timezone.now()
            return sisa_waktu.days
        return 0

# ==========================================
# FUNGSI KOMPRESOR GAMBAR
# ==========================================
def compress_image(image):
    im = Image.open(image)
    if im.mode != 'RGB':
        im = im.convert('RGB')
    max_width = 1000
    if im.width > max_width:
        output_size = (max_width, int(im.height * (max_width/im.width)))
        im.thumbnail(output_size)
    output = BytesIO()
    im.save(output, format='JPEG', quality=60)
    output.seek(0)
    new_image = InMemoryUploadedFile(
        output, 'ImageField', "%s.jpg" % image.name.split('.')[0], 'image/jpeg', sys.getsizeof(output), None
    )
    return new_image

# ==========================================
# 4. TABEL ITEM (Detail Sepatu + Auto Compress)
# ==========================================
class OrderItem(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Baru Masuk'),
        ('PROCESS', 'Sedang Dikerjakan'),
        ('READY', 'Selesai / Siap Ambil'),
        ('COMPLETED', 'Sudah Diambil'),
    ]

    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    service = models.ForeignKey(Service, on_delete=models.PROTECT)
    merk_sepatu = models.CharField(max_length=50)
    warna = models.CharField(max_length=50)
    catatan = models.TextField(blank=True)
    foto_sebelum = models.ImageField(upload_to='foto_sepatu/before/')
    foto_sesudah = models.ImageField(upload_to='foto_sepatu/after/', blank=True, null=True)
    
    # Status Per Sepatu (Baru)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    tanggal_selesai_item = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.merk_sepatu} - {self.service.nama}"

    def save(self, *args, **kwargs):
        if self.foto_sebelum:
            if not self.pk:
                self.foto_sebelum = compress_image(self.foto_sebelum)
            else:
                try:
                    old = OrderItem.objects.get(pk=self.pk)
                    if old.foto_sebelum != self.foto_sebelum:
                        self.foto_sebelum = compress_image(self.foto_sebelum)
                except OrderItem.DoesNotExist:
                    pass
        if self.foto_sesudah:
            if not self.pk:
                 self.foto_sesudah = compress_image(self.foto_sesudah)
            else:
                try:
                    old = OrderItem.objects.get(pk=self.pk)
                    if old.foto_sesudah != self.foto_sesudah:
                        self.foto_sesudah = compress_image(self.foto_sesudah)
                except OrderItem.DoesNotExist:
                    pass
        super().save(*args, **kwargs)

# ==========================================
# 5. TABEL PENGELUARAN (INI YANG HILANG TADI)
# ==========================================
class Pengeluaran(models.Model):
    KATEGORI_CHOICES = [
        ('BAHAN', 'Bahan Baku (Sabun/Cat/Parfum)'),
        ('OPERASIONAL', 'Operasional (Listrik/Bensin/Makan)'),
        ('MARKETING', 'Iklan/Promo/Stiker'),
        ('GAJI', 'Gaji Karyawan'),
        ('LAINNYA', 'Lain-lain'),
    ]

    nama_pengeluaran = models.CharField(max_length=100)
    sub_kategori = models.CharField(max_length=100, blank=True, null=True, help_text="e.g., Sabun, Cat Merah, Bensin, dll")
    biaya = models.DecimalField(max_digits=12, decimal_places=0)
    kategori = models.CharField(max_length=20, choices=KATEGORI_CHOICES, default='BAHAN')
    tanggal = models.DateTimeField(default=timezone.now)
    keterangan = models.TextField(blank=True, null=True)

    def __str__(self):
        if self.sub_kategori:
            return f"{self.nama_pengeluaran} ({self.sub_kategori}) - Rp {self.biaya}"
        return f"{self.nama_pengeluaran} - Rp {self.biaya}"