from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.user_dashboard, name="user_dashboard"),
    path('cars_for_rent/', views.cars_for_rent, name="cars_for_rent"),
    path('car/<str:plate_number>/', views.car_detail, name='car_detail'),
    path('rent/<str:plate_number>/', views.rent_car, name='rent_car'),
    path('user-pending-reservations/', views.pending_reservations, name='user_pending_reservations'),
    path('user-cancel-reservation/', views.cancel_reservation, name='user_cancel_reservation'),
    path('user-approved-reservations/', views.approved_reservations, name='user_approved_reservations'),
    path('user-cancelled-reservations-list/', views.cancelled_reservations_view, name='user_cancelled_reservations'),
    path('history/', views.reservation_history, name='reservation_history'),
    path('verify-email/', views.verify_email_view, name='verify-email'),
    path('resend-verification/', views.resend_verification, name='resend-verification'),
    
]