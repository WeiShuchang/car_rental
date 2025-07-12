from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import UserProfile, Driver, Car, Reservation
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from django.utils.crypto import get_random_string
import random

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = UserProfile
        fields = ['role','contact_number']

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

class SignUpForm(forms.ModelForm):
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    contact_number = forms.CharField(max_length=20, required=True)
    password1 = forms.CharField(widget=forms.PasswordInput, label="Password")
    password2 = forms.CharField(widget=forms.PasswordInput, label="Confirm Password")

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2', 'contact_number']

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords do not match.")
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        user.is_active = False  # User remains inactive until verification
        if commit:
            user.save()
            # Generate a 6-digit verification code (e.g., 456789)
            verification_code = str(random.randint(100000, 999999))
            UserProfile.objects.update_or_create(
                user=user,
                defaults={
                    'role': 'user',
                    'contact_number': self.cleaned_data['contact_number'],
                    'email_verification_code': verification_code,  # Store the code
                }
            )
            # Send verification email
            self.send_verification_email(user, verification_code)
        return user

    def send_verification_email(self, user, verification_code):
        subject = 'Verify Your Email Address'
        message = f"""
        Thank you for registering!
        Your verification code is: **{verification_code}**
        Enter this code on the verification page to activate your account.
        """
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )