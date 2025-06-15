
from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.driver_dashboard, name="driver_dashboard"),
    path('chat/send-message/', views.send_message, name='send_message'),
    path('chat/mark-messages-read/<int:room_id>/',  views.mark_messages_read, name='mark_messages_read'),
    path('chat/get-messages/<int:room_id>/',  views.get_messages, name='get_messages'),
    path('driver/reservations/approved/', views.driver_approved_reservations, name='driver_approved_reservations'),
    path('driver/reservations/completed/', views.driver_completed_reservations, name='driver_completed_reservations'),
]
