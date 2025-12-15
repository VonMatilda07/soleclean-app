from django.shortcuts import render, redirect, get_object_or_404
from .models import Order, Customer, OrderItem, Service
from .forms import CustomerForm, OrderItemForm
from django.contrib import messages
from django.db.models import Sum, Count
from django.utils import timezone
import datetime
import qrcode # <-- Tambahan
from io import BytesIO # <-- Tambahan
import base64 # <-- Tambahan
from django.urls import reverse
from .forms import PengeluaranForm
from .models import Pengeluaran

# ==========================================
# 1. DASHBOARD OPERASIONAL (Teknisi/Kasir)
# ==========================================
def dashboard(request):
    # Tampilkan order yang punya item dengan status BUKAN COMPLETED
    # Urutkan dari order terbaru
    orders = Order.objects.filter(items__status__in=['PENDING', 'PROCESS', 'READY']).distinct().order_by('-tanggal_masuk')
    return render(request, 'dashboard.html', {'orders': orders})

# ==========================================
# 2. DASHBOARD ANALYTICS (Owner/Keuangan)
# ==========================================
def analytics(request):
    # 1. Total Pendapatan Kotor (Semua yang Statusnya COMPLETED)
    total_omzet = Order.objects.filter(status='COMPLETED').aggregate(
        total=Sum('items__service__harga')
    )['total'] or 0

    # 2. Total Pengeluaran (Gaji + Belanja + Listrik)
    total_pengeluaran = Pengeluaran.objects.aggregate(
        total=Sum('biaya')
    )['total'] or 0

    # 3. LABA BERSIH (Rumus Jujur Jepri)
    laba_bersih = total_omzet - total_pengeluaran

    # 4. Breakdown Duit (Biar tau duit di laci harusnya berapa)
    # Hitung cuma dari order yang COMPLETED (Udah bayar)
    duit_cash = Order.objects.filter(status='COMPLETED', metode_pembayaran='CASH').aggregate(total=Sum('items__service__harga'))['total'] or 0
    duit_transfer = Order.objects.filter(status='COMPLETED', metode_pembayaran='TRANSFER').aggregate(total=Sum('items__service__harga'))['total'] or 0

    # 5. Handle Input Pengeluaran
    if request.method == 'POST':
        form = PengeluaranForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('analytics')
    else:
        form = PengeluaranForm()

    list_pengeluaran = Pengeluaran.objects.all().order_by('-tanggal')[:5]

    context = {
        'total_omzet': total_omzet,
        'total_pengeluaran': total_pengeluaran,
        'laba_bersih': laba_bersih,
        'duit_cash': duit_cash,         # <-- Info buat Cek Laci
        'duit_transfer': duit_transfer, # <-- Info buat Cek Mutasi
        'form_pengeluaran': form,
        'list_pengeluaran': list_pengeluaran
    }
    return render(request, 'analytics.html', context)

# ==========================================
# 3. INPUT ORDER (Strict Dropdown)
# ==========================================
def tambah_order(request):
    # Ambil data customer buat dropdown, urutkan dari member terbaru
    customers = Customer.objects.all().order_by('-join_date')

    if request.method == 'POST':
        # Ambil ID Customer dari Dropdown
        customer_id = request.POST.get('customer_id')

        # VALIDASI: Wajib pilih pelanggan
        if not customer_id:
            messages.error(request, '⚠️ Wajib pilih pelanggan! Jika belum ada, klik tombol "+ Pelanggan Baru".')
            return render(request, 'tambah_order.html', {
                'customers': customers,
                'services': Service.objects.all()
            })

        try:
            customer = get_object_or_404(Customer, id=customer_id)
            
            # 1. Buat Order Baru
            order = Order.objects.create(customer=customer)
            
            # 2. Proses Multiple Items dari Formset
            items_added = 0
            
            # Loop semua field yang ada di request
            for key in request.POST.keys():
                # Cari pattern: orderitem_set-X-service
                if key.startswith('orderitem_set-') and key.endswith('-service'):
                    # Extract index dari key
                    parts = key.split('-')
                    if len(parts) >= 3:
                        i = parts[1]
                        
                        # Cek apakah item ini di-delete
                        delete_key = f'orderitem_set-{i}-DELETE'
                        if request.POST.get(delete_key) == 'on':
                            continue
                        
                        # Ambil data dari form
                        service_id = request.POST.get(f'orderitem_set-{i}-service')
                        merk_sepatu = request.POST.get(f'orderitem_set-{i}-merk_sepatu', '').strip()
                        warna = request.POST.get(f'orderitem_set-{i}-warna', '').strip()
                        catatan = request.POST.get(f'orderitem_set-{i}-catatan', '').strip()
                        foto_sebelum = request.FILES.get(f'orderitem_set-{i}-foto_sebelum')
                        
                        # Validasi: minimal ada service dan foto
                        if service_id and foto_sebelum:
                            service = get_object_or_404(Service, id=service_id)
                            
                            # Buat OrderItem
                            item = OrderItem.objects.create(
                                order=order,
                                service=service,
                                merk_sepatu=merk_sepatu or 'N/A',
                                warna=warna or 'N/A',
                                catatan=catatan,
                                foto_sebelum=foto_sebelum
                            )
                            items_added += 1
            
            # Validasi: minimal ada 1 item
            if items_added == 0:
                order.delete()  # Hapus order yang kosong
                messages.error(request, '⚠️ Setiap sepatu WAJIB ada foto! Cek kembali input Anda.')
                return render(request, 'tambah_order.html', {
                    'customers': customers,
                    'services': Service.objects.all()
                })
            
            messages.success(request, f'✅ Order berhasil disimpan! ({items_added} item)')
            return redirect('dashboard')
        
        except Exception as e:
            import traceback
            traceback.print_exc()
            messages.error(request, f'❌ Error: {str(e)}')
            return render(request, 'tambah_order.html', {
                'customers': customers,
                'services': Service.objects.all()
            })
    
    return render(request, 'tambah_order.html', {
        'customers': customers,
        'services': Service.objects.all()
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
# 5. DETAIL & UPDATE STATUS (Per Item - Sepatu)
# ==========================================
def detail_order(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    
    # Hitung total belanja buat ditampilkan/dikirim ke WA
    total_belanja = 0
    for item in order.items.all():
        total_belanja += item.service.harga

    if request.method == 'POST':
        # A. UPDATE STATUS PER ITEM (Sepatu)
        for item in order.items.all():
            status_key = f'status_item_{item.id}'
            status_baru = request.POST.get(status_key)
            
            if status_baru:
                item.status = status_baru
                
                # Catat waktu selesai kalau status READY/COMPLETED
                if status_baru in ['READY', 'COMPLETED']:
                    item.tanggal_selesai_item = timezone.now()
                else:
                    item.tanggal_selesai_item = None
                
                item.save()
            
        # B. UPDATE FOTO AFTER
        for item in order.items.all():
            file_foto = request.FILES.get(f'foto_after_{item.id}') 
            if file_foto:
                item.foto_sesudah = file_foto
                item.save()
        
        return redirect('detail_order', order_id=order.id)

    return render(request, 'detail_order.html', {
        'order': order,
        'total_belanja': total_belanja,
        'status_choices': OrderItem.STATUS_CHOICES
    })

# ==========================================
# 6. CETAK STRUK
# ==========================================
# operasional/views.py

def cetak_struk(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    
    # 1. HITUNG TOTAL HARGA (Logic Baru)
    total_hitung = 0
    for item in order.items.all():
        total_hitung += item.service.harga
    
    # 2. QR CODE GENERATOR (Tetap kita simpan, siapa tau nanti mau dimunculin lagi)
    import qrcode
    from io import BytesIO
    import base64
    
    relative_link = reverse('detail_order', args=[order.id])
    link_tracking = request.build_absolute_uri(relative_link)
    qr = qrcode.QRCode(box_size=4, border=1) # Ukuran dikecilin dikit biar muat
    qr.add_data(link_tracking)
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    img_str = base64.b64encode(buffer.getvalue()).decode()

    # 3. KIRIM KE HTML
    return render(request, 'cetak_struk.html', {
        'order': order,
        'total_hitung': total_hitung, # <-- INI YANG DITUNGGU HTML KAMU
        'qr_code': img_str
    })

# operasional/views.py

# operasional/views.py (Taruh di paling bawah)

def lunasi_order(request, order_id):
    # 1. Cari Ordernya
    order = get_object_or_404(Order, id=order_id)
    
    if request.method == 'POST':
        # 2. Ambil data dari Pop-up (Cash atau Transfer?)
        metode = request.POST.get('metode_pembayaran')
        
        # 3. UPDATE STATUS JADI LUNAS
        order.status = 'COMPLETED'           # Ubah status
        order.metode_pembayaran = metode     # Simpan cara bayar
        order.tanggal_selesai = timezone.now() # Catat jam ambil
        order.save()                         # Simpan ke database
        
        # 4. UPDATE SEMUA ITEMS STATUS JADI COMPLETED (OTOMATIS)
        current_time = timezone.now()
        for item in order.items.all():
            item.status = 'COMPLETED'
            item.tanggal_selesai_item = current_time
            item.save()
        
        # 5. Balik lagi ke halaman detail
        return redirect('detail_order', order_id=order.id)
    
    # Kalau bukan POST, balik aja gak usah ngapa-ngapain
    return redirect('detail_order', order_id=order.id)