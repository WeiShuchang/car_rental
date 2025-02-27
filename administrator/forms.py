from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import UserProfile, Driver, Car, Reservation

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = UserProfile
        fields = ['role']

class DriverForm(forms.ModelForm):
    class Meta:
        model = Driver
        fields = ['license_number', 'phone_number']

class CarForm(forms.ModelForm):
    class Meta:
        model = Car
        fields = '__all__'

class ReservationForm(forms.ModelForm):
    class Meta:
        model = Reservation
        fields = ['car', 'start_date', 'end_date', 'status']
