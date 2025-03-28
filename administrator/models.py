from django.contrib.auth.models import User
from django.db import models
from django.utils.timezone import now
from datetime import timedelta
from django.db.models.signals import post_save
from django.dispatch import receiver

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    ROLE_CHOICES = (
        ('user', 'User'),
        ('driver', 'Driver'),
        ('admin', 'Admin'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='user')
    contact_number = models.CharField(max_length=15, blank=True, null=True)  # New field

    def __str__(self):
        return self.user.username

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    # This single signal handles both creation and updates
    if created:
        UserProfile.objects.get_or_create(user=instance)
    instance.userprofile.save()

class Driver(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    license_number = models.CharField(max_length=50, unique=True)
    phone_number = models.CharField(max_length=15, unique=True)
    image = models.ImageField(upload_to='driver_images/', default='driver_images/default.jpg', blank=True, null=True)
    availability = models.BooleanField(default=True)  # New field for availability

    def __str__(self):
        return f"{self.user.username} - {self.license_number} ({'Available' if self.availability else 'Unavailable'})"

    @classmethod
    def create_driver(cls, username, password, license_number, phone_number, image=None):
        user = User.objects.create_user(username=username, password=password)
        user_profile = user.userprofile
        user_profile.role = 'driver'
        user_profile.save()

        driver = cls.objects.create(
            user=user, 
            license_number=license_number, 
            phone_number=phone_number, 
            image=image,
            availability=True  # Default to available
        )
        return driver
class Car(models.Model):
    BODY_TYPES = (
        ('sedan', 'Sedan'),
        ('suv', 'SUV'),
        ('truck', 'Truck'),
        ('van', 'Van'),
        ('bus', 'Bus'),
    )
    
    brand = models.CharField(max_length=50)
    model = models.CharField(max_length=50)
    year = models.PositiveIntegerField()
    plate_number = models.CharField(max_length=20, unique=True)
    body_type = models.CharField(max_length=10, choices=BODY_TYPES)
    available = models.BooleanField(default=True)
    price_per_day = models.DecimalField(max_digits=10, decimal_places=2, help_text="Price per day in USD")
    image = models.ImageField(upload_to='car_images/', null=True, blank=True)

    def __str__(self):
        return f"{self.brand} {self.model} ({self.plate_number})"
    
class Reservation(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    )

    PAYMENT_CHOICES = (
        ('onsite', 'Onsite'),
        ('gcash', 'GCash'),
    )

    PAYMENT_STATUS_CHOICES = (
        ('not_paid', 'Not Paid Yet'),
        ('paid', 'Paid'),
    )

    CANCELLED_BY_CHOICES = (
        ('user', 'User'),
        ('admin', 'Admin'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    car = models.ForeignKey('Car', on_delete=models.CASCADE)
    driver = models.ForeignKey('Driver', on_delete=models.SET_NULL, null=True, blank=True)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    payment_method = models.CharField(max_length=10, choices=PAYMENT_CHOICES, default='onsite')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    total_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    payment_status = models.CharField(max_length=10, choices=PAYMENT_STATUS_CHOICES, default='not_paid')

    # New fields
    is_cancelled_notif = models.BooleanField(default=False)
    is_approved_notif = models.BooleanField(default=False)
    reason_for_cancelling = models.TextField(blank=True, null=True)
    cancelled_by = models.CharField(max_length=10, choices=CANCELLED_BY_CHOICES, blank=True, null=True)

    def __str__(self):
        return f"Reservation {self.id} - {self.car} by {self.user.username} (₱{self.total_cost}) - {self.get_payment_status_display()}"
