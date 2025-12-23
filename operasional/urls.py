from django.urls import path
from . import views
from operasional.views import dashboard, tambah_order, detail_order, cetak_struk
from operasional.views import lunasi_order, api_analytics_data, user_login, user_logout, track_order

urlpatterns = [
    # Authentication
    path('login/', user_login, name='login'),
    path('logout/', user_logout, name='logout'),
    
    # Main Routes
    path('', views.dashboard, name='dashboard'),
    path('tambah/', views.tambah_order, name='tambah_order'),
    path('order/<int:order_id>/', views.detail_order, name='detail_order'),
    path('track/<int:order_id>/', views.track_order, name='track_order'),
    path('order/<int:order_id>/print/', views.cetak_struk, name='cetak_struk'),
    path('customer/new/', views.tambah_customer, name='tambah_customer'),
    path('analytics/', views.analytics, name='analytics'),
    path('api/analytics/data/', api_analytics_data, name='api_analytics_data'),
    path('order/<int:order_id>/lunasi/', lunasi_order, name='lunasi_order'),
]