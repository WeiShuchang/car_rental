from django.contrib import admin
from .models import User, Driver, Car, Reservation, UserProfile

admin.site.register(UserProfile)
admin.site.register(Driver)
admin.site.register(Car)
admin.site.register(Reservation)
