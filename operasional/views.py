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
    from django.db.models import Q
    from datetime import timedelta
    
    # 1. GET DATE RANGE FILTER
    filter_type = request.GET.get('filter', 'all')  # all, today, week, month, custom
    today = timezone.now().date()
    
    if filter_type == 'today':
        start_date = today
        end_date = today + timedelta(days=1)
        filter_label = 'Hari Ini'
    elif filter_type == 'week':
        start_date = today - timedelta(days=today.weekday())
        end_date = start_date + timedelta(days=7)
        filter_label = 'Minggu Ini'
    elif filter_type == 'month':
        start_date = today.replace(day=1)
        if today.month == 12:
            end_date = today.replace(year=today.year+1, month=1, day=1)
        else:
            end_date = today.replace(month=today.month+1, day=1)
        filter_label = f'Bulan {today.strftime("%B %Y")}'
    else:  # all
        start_date = None
        end_date = None
        filter_label = 'Semua Data'
    
    # 2. Total Pendapatan Kotor (COMPLETED)
    orders_filter = Order.objects.filter(status='COMPLETED')
    if start_date and end_date:
        orders_filter = orders_filter.filter(tanggal_selesai__date__gte=start_date, tanggal_selesai__date__lt=end_date)
    
    total_omzet = orders_filter.aggregate(total=Sum('items__service__harga'))['total'] or 0

    # 3. Total Pengeluaran
    expense_filter = Pengeluaran.objects.all()
    if start_date and end_date:
        expense_filter = expense_filter.filter(tanggal__date__gte=start_date, tanggal__date__lt=end_date)
    
    total_pengeluaran = expense_filter.aggregate(total=Sum('biaya'))['total'] or 0

    # 4. LABA BERSIH
    laba_bersih = total_omzet - total_pengeluaran

    # 5. Breakdown Duit (Cash vs Transfer)
    duit_cash = orders_filter.filter(metode_pembayaran='CASH').aggregate(total=Sum('items__service__harga'))['total'] or 0
    duit_transfer = orders_filter.filter(metode_pembayaran='TRANSFER').aggregate(total=Sum('items__service__harga'))['total'] or 0

    # 6. BREAKDOWN PENGELUARAN BY KATEGORI
    breakdown_pengeluaran = expense_filter.values('kategori').annotate(total=Sum('biaya')).order_by('-total')
    kategori_labels = [item['kategori'] for item in breakdown_pengeluaran]
    kategori_values = [int(item['total']) if item['total'] else 0 for item in breakdown_pengeluaran]  # Convert ke int

    # 7. TOP SERVICES (Paling sering dipesan)
    from operasional.models import Service
    top_services = OrderItem.objects.filter(order__status='COMPLETED')
    if start_date and end_date:
        top_services = top_services.filter(order__tanggal_selesai__date__gte=start_date, order__tanggal_selesai__date__lt=end_date)
    
    top_services = top_services.values('service__nama').annotate(
        count=Count('id'),
        total_revenue=Sum('service__harga')
    ).order_by('-count')[:5]

    # 8. GROWTH CHART DATA (Last 7 atau 30 days)
    if filter_type == 'month':
        days_range = 30
    else:
        days_range = 7
    
    daily_omzet = []
    daily_labels = []
    
    for i in range(days_range, 0, -1):
        date = today - timedelta(days=i)
        day_revenue = Order.objects.filter(
            status='COMPLETED',
            tanggal_selesai__date=date
        ).aggregate(total=Sum('items__service__harga'))['total'] or 0
        
        # Convert ke int untuk JavaScript
        daily_omzet.append(int(day_revenue) if day_revenue else 0)
        daily_labels.append(date.strftime('%d %b'))

    # 9. Handle Input Pengeluaran
    if request.method == 'POST':
        form = PengeluaranForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('analytics')
    else:
        form = PengeluaranForm()

    list_pengeluaran = expense_filter.order_by('-tanggal')[:5]

    context = {
        'total_omzet': total_omzet,
        'total_pengeluaran': total_pengeluaran,
        'laba_bersih': laba_bersih,
        'duit_cash': duit_cash,
        'duit_transfer': duit_transfer,
        'form_pengeluaran': form,
        'list_pengeluaran': list_pengeluaran,
        'filter_type': filter_type,
        'filter_label': filter_label,
        # Breakdown data
        'kategori_labels': kategori_labels,
        'kategori_values': kategori_values,
        # Top services
        'top_services': top_services,
        # Growth chart
        'daily_labels': daily_labels,
        'daily_omzet': daily_omzet,
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