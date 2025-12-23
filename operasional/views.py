from django.shortcuts import render, redirect, get_object_or_404
from .models import Order, Customer, OrderItem, Service
from .forms import CustomerForm, OrderItemForm
from django.contrib import messages
from django.db.models import Sum, Count
from django.utils import timezone
from django.http import JsonResponse
import datetime
import qrcode # <-- Tambahan
from io import BytesIO # <-- Tambahan
import base64 # <-- Tambahan
from django.urls import reverse
from .forms import PengeluaranForm
from .models import Pengeluaran
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import Group
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm

# ==========================================
# AUTHENTICATION VIEWS (LOGIN/LOGOUT)
# ==========================================
def user_login(request):
    """User login view"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                # Set session timeout (optional)
                if request.POST.get('remember_me'):
                    request.session.set_expiry(1209600)  # 2 weeks
                else:
                    request.session.set_expiry(0)  # Browser close
                
                messages.success(request, f'Selamat datang, {username}! 👋')
                return redirect('dashboard')
    else:
        form = AuthenticationForm()
    
    return render(request, 'login.html', {'form': form})

@login_required
def user_logout(request):
    """User logout view"""
    username = request.user.username
    logout(request)
    messages.success(request, f'Anda telah logout. Sampai jumpa, {username}! 👋')
    return redirect('login')

# ==========================================
# RBAC HELPER FUNCTIONS
# ==========================================
def is_admin(user):
    """Check if user is in Admin group"""
    return user.is_staff or user.groups.filter(name='Admin').exists()

def is_supervisor(user):
    """Check if user is in Supervisor group"""
    return user.groups.filter(name__in=['Supervisor', 'Admin']).exists()

def is_teknisi(user):
    """Check if user is in Teknisi group"""
    return user.groups.filter(name__in=['Teknisi', 'Admin']).exists()

def can_add_order(user):
    """Supervisor, Teknisi or Admin can add orders"""
    return is_admin(user) or is_supervisor(user) or is_teknisi(user)

# ==========================================
# 1. DASHBOARD OPERASIONAL (Teknisi/Kasir)
# ==========================================
@login_required
def dashboard(request):
    # Tampilkan order yang punya item dengan status BUKAN COMPLETED
    # Urutkan dari order terbaru
    orders = Order.objects.filter(items__status__in=['PENDING', 'PROCESS', 'READY']).distinct().order_by('-tanggal_masuk')
    return render(request, 'dashboard.html', {'orders': orders})

# ==========================================
# 2. DASHBOARD ANALYTICS (Supervisor/Admin)
# ==========================================
@login_required
@user_passes_test(is_supervisor, login_url='dashboard')
def analytics(request):
    from django.db.models import Q
    from datetime import timedelta
    
    # 1. GET DATE RANGE FILTER
    filter_type = request.GET.get('filter', 'all')  # all, today, week, month, custom
    today = timezone.now().date()
    
    # Get custom date range if provided
    custom_start = request.GET.get('start_date')
    custom_end = request.GET.get('end_date')
    
    if filter_type == 'today':
        start_date = today
        end_date = today + timedelta(days=1)
        filter_label = 'Hari Ini'
        # For date picker display
        display_start_date = today.strftime('%Y-%m-%d')
        display_end_date = today.strftime('%Y-%m-%d')
    elif filter_type == 'week':
        start_date = today - timedelta(days=today.weekday())
        end_date = start_date + timedelta(days=7)
        filter_label = 'Minggu Ini'
        # For date picker display
        display_start_date = start_date.strftime('%Y-%m-%d')
        display_end_date = (end_date - timedelta(days=1)).strftime('%Y-%m-%d')
    elif filter_type == 'month':
        start_date = today.replace(day=1)
        if today.month == 12:
            end_date = today.replace(year=today.year+1, month=1, day=1)
        else:
            end_date = today.replace(month=today.month+1, day=1)
        filter_label = f'Bulan {today.strftime("%B %Y")}'
        # For date picker display
        display_start_date = start_date.strftime('%Y-%m-%d')
        display_end_date = (end_date - timedelta(days=1)).strftime('%Y-%m-%d')
    elif filter_type == 'custom' and custom_start and custom_end:
        # Custom date range
        try:
            from datetime import datetime
            start_date = datetime.strptime(custom_start, '%Y-%m-%d').date()
            end_date = datetime.strptime(custom_end, '%Y-%m-%d').date() + timedelta(days=1)
            filter_label = f'Rentang {start_date.strftime("%d %b %Y")} - {(end_date - timedelta(days=1)).strftime("%d %b %Y")}'
            # For date picker display
            display_start_date = custom_start
            display_end_date = custom_end
        except:
            start_date = None
            end_date = None
            filter_label = 'Semua Data'
            display_start_date = today.strftime('%Y-%m-%d')
            display_end_date = today.strftime('%Y-%m-%d')
    else:  # all
        start_date = None
        end_date = None
        filter_label = 'Semua Data'
        display_start_date = today.strftime('%Y-%m-%d')
        display_end_date = today.strftime('%Y-%m-%d')
    
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

    # 6b. BREAKDOWN PENGELUARAN BY SUB_KATEGORI (with counts)
    sub_kategori_breakdown = expense_filter.values('sub_kategori').annotate(
        total=Sum('biaya'),
        count=Count('id')
    ).order_by('-count')
    # Filter out items where sub_kategori is null/empty and calculate average
    sub_kategori_breakdown_list = []
    for item in sub_kategori_breakdown:
        if item['sub_kategori']:
            item['average'] = int(item['total'] / item['count']) if item['count'] > 0 else 0
            sub_kategori_breakdown_list.append(item)
    sub_kategori_breakdown = sub_kategori_breakdown_list

    # 7. TOP SERVICES (Paling sering dipesan)
    from operasional.models import Service
    top_services = OrderItem.objects.filter(order__status='COMPLETED')
    if start_date and end_date:
        top_services = top_services.filter(order__tanggal_selesai__date__gte=start_date, order__tanggal_selesai__date__lt=end_date)
    
    top_services = top_services.values('service__nama').annotate(
        count=Count('id'),
        total_revenue=Sum('service__harga')
    ).order_by('-count')[:5]

    # 8. GROWTH CHART DATA - Respect the selected date range filter
    # Determine the actual date range for chart/breakdown
    if start_date and end_date:
        chart_start_date = start_date
        chart_end_date = end_date - timedelta(days=1)  # Convert back to inclusive end date
    else:
        # For 'all' filter, show last 7 or 30 days
        if filter_type == 'month':
            chart_start_date = today - timedelta(days=30)
        else:
            chart_start_date = today - timedelta(days=7)
        chart_end_date = today
    
    daily_omzet = []
    daily_labels = []
    daily_breakdown = []  # Untuk tabel hari per hari
    
    # Calculate number of days between start and end
    current_date = chart_start_date
    while current_date <= chart_end_date:
        day_revenue = Order.objects.filter(
            status='COMPLETED',
            tanggal_selesai__date=current_date
        ).aggregate(total=Sum('items__service__harga'))['total'] or 0
        
        # Convert ke int untuk JavaScript
        daily_omzet.append(int(day_revenue) if day_revenue else 0)
        daily_labels.append(current_date.strftime('%d %b'))
        
        # Breakdown per hari
        daily_breakdown.append({
            'tanggal': current_date,
            'tanggal_format': current_date.strftime('%A, %d %B %Y'),
            'omzet': int(day_revenue) if day_revenue else 0,
            'item_count': Order.objects.filter(
                status='COMPLETED',
                tanggal_selesai__date=current_date
            ).aggregate(count=Count('items'))['count'] or 0
        })
        current_date += timedelta(days=1)

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
        'sub_kategori_breakdown': sub_kategori_breakdown,
        # Top services
        'top_services': top_services,
        # Growth chart
        'daily_labels': daily_labels,
        'daily_omzet': daily_omzet,
        # Date picker values - ALWAYS synced with current filter
        'display_start_date': display_start_date,
        'display_end_date': display_end_date,
        # Daily breakdown
        'daily_breakdown': daily_breakdown,
    }
    return render(request, 'analytics.html', context)

# ==========================================
# 3. INPUT ORDER (Strict Dropdown)
# ==========================================
@login_required
@user_passes_test(can_add_order, login_url='dashboard')
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
@login_required
@user_passes_test(is_admin, login_url='dashboard')
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
@login_required
def detail_order(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    
    # Hitung total belanja buat ditampilkan/dikirim ke WA
    total_belanja = 0
    for item in order.items.all():
        total_belanja += item.service.harga

    if request.method == 'POST':
        # Only teknisi or admin may perform status/photo updates
        if not (is_teknisi(request.user) or is_admin(request.user)):
            messages.error(request, '⚠️ Anda tidak memiliki akses untuk mengubah status sepatu.')
            return redirect('detail_order', order_id=order.id)

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

@login_required
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
    
    # Public tracking link for customer (no login required)
    relative_link = reverse('track_order', args=[order.id])
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


def track_order(request, order_id):
    """Public tracking view for customers (no login required). Read-only."""
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'track_order.html', {'order': order})

# operasional/views.py

# operasional/views.py (Taruh di paling bawah)

@login_required
@user_passes_test(is_supervisor, login_url='dashboard')
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

# ==========================================
# 7. JSON API ENDPOINT - Analytics Data
# ==========================================

@login_required
@user_passes_test(is_supervisor, login_url='dashboard')
def api_analytics_data(request):
    """
    JSON endpoint untuk chart data
    Support query params:
    - filter: today, week, month, custom
    - start_date: YYYY-MM-DD (for custom)
    - end_date: YYYY-MM-DD (for custom)
    """
    from datetime import timedelta
    import json
    
    filter_type = request.GET.get('filter', 'month')
    custom_start = request.GET.get('start_date')
    custom_end = request.GET.get('end_date')
    today = timezone.now().date()
    
    # Determine date range
    if filter_type == 'today':
        start_date = today
        end_date = today + timedelta(days=1)
    elif filter_type == 'week':
        start_date = today - timedelta(days=today.weekday())
        end_date = start_date + timedelta(days=7)
    elif filter_type == 'month':
        start_date = today.replace(day=1)
        if today.month == 12:
            end_date = today.replace(year=today.year+1, month=1, day=1)
        else:
            end_date = today.replace(month=today.month+1, day=1)
    elif filter_type == 'custom' and custom_start and custom_end:
        try:
            from datetime import datetime
            start_date = datetime.strptime(custom_start, '%Y-%m-%d').date()
            end_date = datetime.strptime(custom_end, '%Y-%m-%d').date() + timedelta(days=1)
        except:
            return JsonResponse({'error': 'Invalid date format'}, status=400)
    else:
        return JsonResponse({'error': 'Invalid filter'}, status=400)
    
    # Calculate chart data
    chart_start_date = start_date
    chart_end_date = end_date - timedelta(days=1)
    
    daily_omzet = []
    daily_labels = []
    
    current_date = chart_start_date
    while current_date <= chart_end_date:
        day_revenue = Order.objects.filter(
            status='COMPLETED',
            tanggal_selesai__date=current_date
        ).aggregate(total=Sum('items__service__harga'))['total'] or 0
        
        daily_omzet.append(int(day_revenue) if day_revenue else 0)
        daily_labels.append(current_date.strftime('%d %b'))
        current_date += timedelta(days=1)
    
    # Breakdown pengeluaran by kategori
    expense_filter = Pengeluaran.objects.filter(
        tanggal__date__gte=start_date,
        tanggal__date__lt=end_date
    )
    breakdown_pengeluaran = expense_filter.values('kategori').annotate(total=Sum('biaya')).order_by('-total')
    kategori_labels = [item['kategori'] for item in breakdown_pengeluaran]
    kategori_values = [int(item['total']) if item['total'] else 0 for item in breakdown_pengeluaran]
    
    # KPI data
    orders_filter = Order.objects.filter(status='COMPLETED')
    orders_filter = orders_filter.filter(tanggal_selesai__date__gte=start_date, tanggal_selesai__date__lt=end_date)
    
    total_omzet = orders_filter.aggregate(total=Sum('items__service__harga'))['total'] or 0
    total_pengeluaran = expense_filter.aggregate(total=Sum('biaya'))['total'] or 0
    laba_bersih = total_omzet - total_pengeluaran
    
    duit_cash = orders_filter.filter(metode_pembayaran='CASH').aggregate(total=Sum('items__service__harga'))['total'] or 0
    duit_transfer = orders_filter.filter(metode_pembayaran='TRANSFER').aggregate(total=Sum('items__service__harga'))['total'] or 0
    
    # Get expense history (5 latest)
    list_pengeluaran = expense_filter.order_by('-tanggal')[:5]
    pengeluaran_data = []
    for expense in list_pengeluaran:
        pengeluaran_data.append({
            'tanggal': expense.tanggal.strftime('%d %b'),
            'nama': expense.nama_pengeluaran,
            'sub_kategori': expense.sub_kategori or '',
            'kategori_display': expense.get_kategori_display(),
            'biaya': int(expense.biaya),
        })
    
    return JsonResponse({
        'status': 'success',
        'filter_type': filter_type,
        'kpi': {
            'total_omzet': int(total_omzet),
            'total_pengeluaran': int(total_pengeluaran),
            'laba_bersih': int(laba_bersih),
            'duit_cash': int(duit_cash),
            'duit_transfer': int(duit_transfer),
        },
        'charts': {
            'daily_labels': daily_labels,
            'daily_omzet': daily_omzet,
            'kategori_labels': kategori_labels,
            'kategori_values': kategori_values,
        },
        'expense_history': pengeluaran_data,
    })