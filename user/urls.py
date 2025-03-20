from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.user_dashboard, name="user_dashboard"),
    path('cars_for_rent/', views.cars_for_rent, name="cars_for_rent"),
    path('car/<str:plate_number>/', views.car_detail, name='car_detail'),
]