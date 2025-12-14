from django import forms
from .models import Customer, OrderItem

# Form Data Pelanggan
class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['nama', 'whatsapp', 'alamat']
        widgets = {
            'nama': forms.TextInput(attrs={'class': 'w-full border p-2 rounded', 'placeholder': 'Nama Customer'}),
            'whatsapp': forms.TextInput(attrs={'class': 'w-full border p-2 rounded', 'placeholder': '628xxx (Wajib Unik)'}),
            'alamat': forms.Textarea(attrs={'class': 'w-full border p-2 rounded', 'rows': 2, 'placeholder': 'Alamat (Opsional)'}),
        }

# Form Detail Sepatu (Tetap sama)
class OrderItemForm(forms.ModelForm):
    class Meta:
        model = OrderItem
        fields = ['service', 'merk_sepatu', 'warna', 'foto_sebelum', 'catatan']
        widgets = {
            'service': forms.Select(attrs={'class': 'w-full border p-2 rounded'}),
            'merk_sepatu': forms.TextInput(attrs={'class': 'w-full border p-2 rounded'}),
            'warna': forms.TextInput(attrs={'class': 'w-full border p-2 rounded'}),
            'catatan': forms.Textarea(attrs={'class': 'w-full border p-2 rounded', 'rows': 2}),
        }