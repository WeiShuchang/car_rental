from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path('', views.admin_dashboard, name="admin_dashboard"),
    path('pending-reservations/', views.pending_reservations, name='pending_reservations'),
    path('reservation/<int:reservation_id>/approve/', views.approve_reservation, name='approve_reservation'),
    path('reservation/<int:reservation_id>/cancel/', views.cancel_reservation, name='cancel_reservation'),
    path("cancel-reservation/", views.cancel_reservation, name="cancel_reservation"),
    path('approved-reservations/', views.approved_reservations, name='approved_reservations'),
    path('cancelled-reservations/', views.cancelled_reservations, name='cancelled_reservations'),
    path("complete-reservation/<int:reservation_id>/", views.complete_reservation, name="complete_reservation"),
    path('completed-travels/', views.completed_reservations, name='completed_reservations'),
    path('reservations/<int:reservation_id>/update-payment/', views.update_payment_status, name='update_payment_status'),

]
