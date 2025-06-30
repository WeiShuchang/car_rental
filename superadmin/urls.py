from django.urls import path
from . import views

urlpatterns = [
    
    path('', views.superadmin_dashboard, name="superadmin_dashboard"),
    path('cars/', views.car_list, name='car_list'),
    path('users/', views.all_users_list, name='all_users_list'),
    path('admins/', views.all_admins_list, name='all_admins_list'),
    path('reservations/all/', views.all_reservations, name='all_reservations'),
    path('adding-admin/', views.add_admin, name='add_admin'),
    path('add-car/', views.add_car, name='add_car'),
    path('delete-car/<int:car_id>/', views.delete_car, name='delete_car'),
    path('cars/<int:car_id>/edit/', views.edit_car, name='edit_car'),
    path('drivers/', views.driver_list, name='driver_list'),
    path('add-driver/', views.add_driver, name='add_driver'),
    path('delete-driver/<int:driver_id>/', views.delete_driver, name='delete_driver'),
    path('drivers/update/<int:driver_id>/', views.update_driver, name='update_driver'),
    path('reservations/report/', views.generate_reservations_pdf, name='reservations_report'),
    
    path('pending-reservations/', views.pending_reservations, name='superadmin_pending_reservations'),
    path('reservation/<int:reservation_id>/approve/', views.approve_reservation, name='superadmin_approve_reservation'),
    path('reservation/<int:reservation_id>/cancel/', views.cancel_reservation, name='superadmin_cancel_reservation'),
    path("cancel-reservation/", views.cancel_reservation, name="superadmin_cancel_reservation"),
    path('approved-reservations/', views.approved_reservations, name='superadmin_approved_reservations'),
    path('cancelled-reservations/', views.cancelled_reservations, name='superadmin_cancelled_reservations'),
    path("complete-reservation/<int:reservation_id>/", views.complete_reservation, name="superadmin_complete_reservation"),
    path('completed-travels/', views.completed_reservations, name='superadmin_completed_reservations'),
    path('reservations/<int:reservation_id>/update-payment/', views.update_payment_status, name='superadmin_update_payment_status'),
]
