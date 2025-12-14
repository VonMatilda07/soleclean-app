from django.db import models
from django.utils import timezone

# 1. TABEL BARU: Database Pelanggan (CRM)
class Customer(models.Model):
    nama = models.CharField(max_length=100)
    whatsapp = models.CharField(max_length=15, unique=True) # Nomor WA jadi ID unik
    alamat = models.TextField(blank=True, null=True)
    join_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nama} ({self.whatsapp})"

# 2. TABEL SERVICE (Tetap)
class Service(models.Model):
    nama = models.CharField(max_length=100)
    harga = models.DecimalField(max_digits=10, decimal_places=0)
    durasi_hari = models.IntegerField(default=3)
    
    def __str__(self):
        return f"{self.nama} - Rp {self.harga}"

# 3. TABEL ORDER (Diupdate)
class Order(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Baru Masuk'),
        ('PROCESS', 'Sedang Dikerjakan'),
        ('READY', 'Selesai / Siap Ambil'),
        ('COMPLETED', 'Sudah Diambil'),
    ]

    # HAPUS field nama & wa lama, GANTI dengan Link ke Customer
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='orders')
    
    tanggal_masuk = models.DateTimeField(default=timezone.now)
    tanggal_selesai = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')

    def __str__(self):
        return f"Order #{self.id} - {self.customer.nama}"

# 4. TABEL ITEM (Tetap)
class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    service = models.ForeignKey(Service, on_delete=models.PROTECT)
    merk_sepatu = models.CharField(max_length=50)
    warna = models.CharField(max_length=50)
    catatan = models.TextField(blank=True)
    foto_sebelum = models.ImageField(upload_to='foto_sepatu/before/')
    foto_sesudah = models.ImageField(upload_to='foto_sepatu/after/', blank=True, null=True)
    
    def __str__(self):
        return f"{self.merk_sepatu} - {self.service.nama}"