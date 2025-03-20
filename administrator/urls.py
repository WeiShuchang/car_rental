from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path('', views.admin_dashboard, name="admin_dashboard"),
    path('cars/', views.car_list, name='car_list'),
    path('add-car/', views.add_car, name='add_car'),
    path("delete-car/<int:car_id>/", views.delete_car, name="delete_car"),
    path("cars/<int:car_id>/edit/", views.edit_car, name="edit_car"),
    path('drivers/', views.driver_list, name='driver_list'),
    path("add-driver/", views.add_driver, name="add_driver"),
    path('delete-driver/<int:driver_id>/', views.delete_driver, name='delete_driver'),
    path('drivers/update/<int:driver_id>/', views.update_driver, name='update_driver'),
    path('signup/', views.signup_view, name='signup'),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
]
