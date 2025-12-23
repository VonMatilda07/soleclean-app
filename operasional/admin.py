from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Customer, Service, Order, OrderItem, Pengeluaran

# ==========================================
# USER MANAGEMENT (RBAC)
# ==========================================
class UserAdmin(BaseUserAdmin):
    """Customized User Admin untuk manage roles/groups"""
    list_display = ('username', 'email', 'first_name', 'last_name', 'get_groups', 'is_staff')
    list_filter = ('is_staff', 'is_superuser', 'groups')
    filter_horizontal = ('groups', 'user_permissions')
    
    @admin.display(description='Role')
    def get_groups(self, obj):
        return ', '.join([g.name for g in obj.groups.all()]) or 'No Role'

# Unregister default User admin, register custom
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

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

# 3. Pengeluaran Admin
@admin.register(Pengeluaran)
class PengeluaranAdmin(admin.ModelAdmin):
    list_display = ('tanggal', 'nama_pengeluaran', 'kategori', 'sub_kategori', 'biaya')
    list_filter = ('tanggal', 'kategori')
    search_fields = ('nama_pengeluaran', 'sub_kategori')

# 4. Sisanya Tetap
admin.site.register(Service)
admin.site.register(OrderItem)