from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import UserProfile, Driver, Car, Reservation
from django.contrib.auth.models import User

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = UserProfile
        fields = ['role']

class DriverForm(forms.ModelForm):
    username = forms.CharField(max_length=150, required=True, label="Username")
    first_name = forms.CharField(max_length=30, required=True, label="First Name")
    last_name = forms.CharField(max_length=30, required=True, label="Last Name")
    email = forms.EmailField(required=True, label="Email")
    password = forms.CharField(widget=forms.PasswordInput, required=True, label="Password")

    class Meta:
        model = Driver
        fields = ['license_number', 'phone_number']

    def save(self, commit=True):
        # Create the User instance
        user = User.objects.create_user(
            username=self.cleaned_data['username'],
            first_name=self.cleaned_data['first_name'],
            last_name=self.cleaned_data['last_name'],
            email=self.cleaned_data['email'],
            password=self.cleaned_data['password']
        )

        # Assign role as 'driver' in UserProfile
        user_profile = UserProfile.objects.create(user=user, role='driver')

        # Create Driver instance and link it to the user
        driver = super().save(commit=False)
        driver.user = user
        if commit:
            driver.save()
        return driver
        
class CarForm(forms.ModelForm):
    class Meta:
        model = Car
        fields = '__all__'

class ReservationForm(forms.ModelForm):
    class Meta:
        model = Reservation
        fields = ['car', 'start_date', 'end_date', 'status']
