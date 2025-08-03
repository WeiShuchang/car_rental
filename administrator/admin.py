from django.contrib import admin
from .models import User, Driver, Car, Reservation, UserProfile, ChatRoom, Message, CarImage

admin.site.register(UserProfile)
admin.site.register(Driver)
admin.site.register(Car)
admin.site.register(Reservation)
admin.site.register(ChatRoom)
admin.site.register(Message)
admin.site.register(CarImage)
