from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('tambah/', views.tambah_order, name='tambah_order'),
    path('order/<int:order_id>/', views.detail_order, name='detail_order'),
    path('order/<int:order_id>/print/', views.cetak_struk, name='cetak_struk'),
    path('customer/new/', views.tambah_customer, name='tambah_customer'),
    path('analytics/', views.analytics, name='analytics'),
]