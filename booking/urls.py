from django.urls import path
from .views import (
    login_view,
    register_view,
    profile_view,
    change_password,
    profile_history,
    get_booking,
    menuLayanan,
    transaksi_list,
    laporan_pendapatan,
    dashboard_summary,
    profile_statistic,
    customer_list,
    
)

urlpatterns = [
    path('login/', login_view),
    path('register/', register_view),
    
    path('profile/', profile_view),
    
    path("profile/password/", change_password),
    
    path('profile/history/', profile_history),
    
    path("customer/", customer_list),
    
    path("profile/statistic/",profile_statistic),

    path('booking/', get_booking),
    path('booking/<int:id>/', get_booking),

    path("transaksi/", transaksi_list),

    path('laporan/', laporan_pendapatan),

    path('dashboard/', dashboard_summary),

    path('layanan/', menuLayanan),
    path('layanan/<int:id>/', menuLayanan),
]