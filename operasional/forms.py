from django import forms
from django.forms import inlineformset_factory 
from .models import Customer, Order, OrderItem, Pengeluaran

# ==========================================
# 1. FORM DATA PELANGGAN
# ==========================================
class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['nama', 'whatsapp', 'alamat']
        widgets = {
            'nama': forms.TextInput(attrs={'class': 'w-full border p-2 rounded', 'placeholder': 'Nama Customer'}),
            'whatsapp': forms.TextInput(attrs={'class': 'w-full border p-2 rounded', 'placeholder': '628xxx (Wajib Unik)'}),
            'alamat': forms.Textarea(attrs={'class': 'w-full border p-2 rounded', 'rows': 2, 'placeholder': 'Alamat (Opsional)'}),
        }

    def clean_whatsapp(self):
        whatsapp = self.cleaned_data.get('whatsapp')
        
        # Cek apakah nomor WhatsApp sudah terdaftar
        if whatsapp:
            # Jika editing customer, exclude customer yang sedang diedit
            if self.instance.pk:
                if Customer.objects.filter(whatsapp=whatsapp).exclude(pk=self.instance.pk).exists():
                    raise forms.ValidationError(
                        "⚠️ Nomor WhatsApp ini sudah terdaftar! Gunakan nomor yang berbeda."
                    )
            else:
                # Jika tambah customer baru
                if Customer.objects.filter(whatsapp=whatsapp).exists():
                    raise forms.ValidationError(
                        "⚠️ Nomor WhatsApp ini sudah terdaftar! Gunakan nomor yang berbeda."
                    )
        
        return whatsapp

# ==========================================
# 2. FORM UTAMA ORDER (Status & Payment)
# ==========================================
class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        # REVISI: Hapus 'customer' dari sini biar gak bentrok saat nambah pelanggan baru
        fields = ['status', 'metode_pembayaran'] 
        widgets = {
            'status': forms.Select(attrs={'class': 'w-full p-2 border rounded'}),
            'metode_pembayaran': forms.Select(attrs={'class': 'w-full p-2 border rounded font-bold bg-yellow-50'}),
        }

# ==========================================
# 3. FORM ITEM SEPATU
# ==========================================
class OrderItemForm(forms.ModelForm):
    class Meta:
        model = OrderItem
        fields = ['service', 'merk_sepatu', 'warna', 'foto_sebelum', 'catatan']
        widgets = {
            'service': forms.Select(attrs={'class': 'w-full p-2 border rounded'}),
            'merk_sepatu': forms.TextInput(attrs={'class': 'w-full p-2 border rounded', 'placeholder': 'Contoh: Nike Air Jordan'}),
            'warna': forms.TextInput(attrs={'class': 'w-full p-2 border rounded', 'placeholder': 'Putih'}),
            'foto_sebelum': forms.ClearableFileInput(attrs={'class': 'w-full text-sm text-gray-500'}),
            'catatan': forms.Textarea(attrs={'class': 'w-full p-2 border rounded', 'rows': 1, 'placeholder': 'Note khusus...'}),
        }

# ==========================================
# 4. FORMSET (Biar bisa input banyak sepatu)
# ==========================================
OrderItemFormSet = inlineformset_factory(
    Order, OrderItem, form=OrderItemForm,
    extra=1, can_delete=True
)

# ==========================================
# 5. FORM PENGELUARAN (Keuangan)
# ==========================================
class PengeluaranForm(forms.ModelForm):
    class Meta:
        model = Pengeluaran
        fields = ['nama_pengeluaran', 'sub_kategori', 'biaya', 'kategori', 'keterangan']
        widgets = {
            'nama_pengeluaran': forms.TextInput(attrs={'class': 'w-full p-2 border rounded', 'placeholder': 'Contoh: Beli Sabun'}),
            'sub_kategori': forms.TextInput(attrs={'class': 'w-full p-2 border rounded', 'placeholder': 'Contoh: Sabun Putih, Cat Merah (opsional)'}),
            'biaya': forms.NumberInput(attrs={'class': 'w-full p-2 border rounded', 'placeholder': '0'}),
            'kategori': forms.Select(attrs={'class': 'w-full p-2 border rounded'}),
            'keterangan': forms.Textarea(attrs={'class': 'w-full p-2 border rounded', 'rows': 2}),
        }