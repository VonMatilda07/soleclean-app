from django.contrib import admin
from .models import Customer, Service, Order, OrderItem

# 1. Daftarin Customer biar bisa diedit manual
@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('nama', 'whatsapp', 'join_date')
    search_fields = ('nama', 'whatsapp')

# 2. Update Order Admin
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    # GANTI 'nama_pelanggan' & 'whatsapp' dengan method baru di bawah
    list_display = ('id', 'get_customer_nama', 'get_customer_wa', 'status', 'tanggal_masuk')
    list_filter = ('status', 'tanggal_masuk')
    search_fields = ('customer__nama', 'customer__whatsapp') # Bisa search by nama customer
    inlines = [OrderItemInline]

    # Teknik buat nampilin field dari tabel tetangga (Customer)
    @admin.display(description='Nama Pelanggan')
    def get_customer_nama(self, obj):
        return obj.customer.nama

    @admin.display(description='WhatsApp')
    def get_customer_wa(self, obj):
        return obj.customer.whatsapp

# 3. Sisanya Tetap
admin.site.register(Service)
admin.site.register(OrderItem)