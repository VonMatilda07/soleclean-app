from django.urls import path
from . import views
from operasional.views import dashboard, tambah_order, detail_order, cetak_struk # <-- Panggil cetak_struk
from operasional.views import lunasi_order

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('tambah/', views.tambah_order, name='tambah_order'),
    path('order/<int:order_id>/', views.detail_order, name='detail_order'),
    path('order/<int:order_id>/print/', views.cetak_struk, name='cetak_struk'),
    path('customer/new/', views.tambah_customer, name='tambah_customer'),
    path('analytics/', views.analytics, name='analytics'),
    path('order/<int:order_id>/print/', cetak_struk, name='cetak_struk'),
    path('order/<int:order_id>/lunasi/', lunasi_order, name='lunasi_order'),
]