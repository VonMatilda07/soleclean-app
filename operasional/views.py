from django.shortcuts import render, redirect, get_object_or_404
from .models import Order, Customer, OrderItem
from .forms import CustomerForm, OrderItemForm
from django.contrib import messages
from django.db.models import Sum, Count
from django.utils import timezone
import datetime

# ==========================================
# 1. DASHBOARD OPERASIONAL (Teknisi/Kasir)
# ==========================================
def dashboard(request):
    # Cuma nampilin order yang BELUM selesai (Antrian Kerja)
    # Diurutkan dari yang paling baru masuk
    orders = Order.objects.exclude(status='COMPLETED').order_by('-tanggal_masuk')
    return render(request, 'dashboard.html', {'orders': orders})

# ==========================================
# 2. DASHBOARD ANALYTICS (Owner/Keuangan)
# ==========================================
def analytics(request):
    now = timezone.now()
    hari_ini = now.date()
    bulan_ini = now.month
    tahun_ini = now.year

    # KONSEP CASH BASIS:
    # Duit dihitung cuma kalau status = 'COMPLETED' (Udah diambil & bayar)
    # Dan filternya berdasarkan 'tanggal_selesai', bukan 'tanggal_masuk'

    # A. Omzet Hari Ini
    omzet_harian = OrderItem.objects.filter(
        order__status='COMPLETED',
        order__tanggal_selesai__date=hari_ini
    ).aggregate(total=Sum('service__harga'))['total'] or 0

    # B. Omzet Bulan Ini
    omzet_bulanan = OrderItem.objects.filter(
        order__status='COMPLETED',
        order__tanggal_selesai__month=bulan_ini,
        order__tanggal_selesai__year=tahun_ini
    ).aggregate(total=Sum('service__harga'))['total'] or 0

    # C. Total Item Selesai Bulan Ini (Performa Toko)
    qty_sepatu_selesai = OrderItem.objects.filter(
        order__status='COMPLETED',
        order__tanggal_selesai__month=bulan_ini,
        order__tanggal_selesai__year=tahun_ini
    ).count()

    return render(request, 'analytics.html', {
        'omzet_harian': omzet_harian,
        'omzet_bulanan': omzet_bulanan,
        'qty_selesai': qty_sepatu_selesai,
        'now': now
    })

# ==========================================
# 3. INPUT ORDER (Strict Dropdown)
# ==========================================
def tambah_order(request):
    # Ambil data customer buat dropdown, urutkan dari member terbaru
    customers = Customer.objects.all().order_by('-join_date')

    if request.method == 'POST':
        form_item = OrderItemForm(request.POST, request.FILES)
        
        # Ambil ID Customer dari Dropdown
        customer_id = request.POST.get('customer_id')

        # VALIDASI: Wajib pilih pelanggan
        if not customer_id:
            messages.error(request, '⚠️ Wajib pilih pelanggan! Jika belum ada, klik tombol "+ Pelanggan Baru".')
            return render(request, 'tambah_order.html', {
                'form_item': form_item,
                'customers': customers
            })

        if form_item.is_valid():
            # Ambil object customer asli
            customer = get_object_or_404(Customer, id=customer_id)

            # 1. Buat Order Baru
            order = Order.objects.create(customer=customer)
            
            # 2. Simpan Item Sepatu
            item = form_item.save(commit=False)
            item.order = order
            item.save()
            
            messages.success(request, 'Order berhasil disimpan! ✅')
            return redirect('dashboard')
        
        else:
            return render(request, 'tambah_order.html', {
                'form_item': form_item,
                'customers': customers
            })
    
    else:
        form_item = OrderItemForm()
    
    return render(request, 'tambah_order.html', {
        'form_item': form_item,
        'customers': customers 
    })

# ==========================================
# 4. TAMBAH PELANGGAN BARU
# ==========================================
def tambah_customer(request):
    if request.method == 'POST':
        form = CustomerForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Pelanggan berhasil didaftarkan! Silakan pilih di dropdown.')
            return redirect('tambah_order')
    else:
        form = CustomerForm()

    return render(request, 'tambah_customer.html', {'form': form})

# ==========================================
# 5. DETAIL & UPDATE STATUS (Logic Tanggal Selesai)
# ==========================================
def detail_order(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    
    # Hitung total belanja buat ditampilkan/dikirim ke WA
    total_belanja = 0
    for item in order.items.all():
        total_belanja += item.service.harga

    if request.method == 'POST':
        # A. UPDATE STATUS
        status_baru = request.POST.get('status')
        if status_baru:
            order.status = status_baru
            
            # LOGIC PENTING: Catat waktu selesai kalau status COMPLETED
            if status_baru == 'COMPLETED':
                order.tanggal_selesai = timezone.now()
            else:
                # Kalau status dibalikin (misal kepencet), hapus tanggal selesainya
                order.tanggal_selesai = None
            
            order.save()
            
        # B. UPDATE FOTO AFTER
        for item in order.items.all():
            file_foto = request.FILES.get(f'foto_after_{item.id}') 
            if file_foto:
                item.foto_sesudah = file_foto
                item.save()
        
        return redirect('detail_order', order_id=order.id)

    return render(request, 'detail_order.html', {
        'order': order,
        'total_belanja': total_belanja
    })

# ==========================================
# 6. CETAK STRUK
# ==========================================
def cetak_struk(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    
    total = 0
    for item in order.items.all():
        total += item.service.harga
    
    return render(request, 'cetak_struk.html', {
        'order': order, 
        'total_hitung': total
    })