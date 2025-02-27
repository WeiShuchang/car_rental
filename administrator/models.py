from django.contrib.auth.models import User
from django.db import models
from django.utils.timezone import now
from datetime import timedelta

# Custom User Model
class UserProfile(models.Model):  
    user = models.OneToOneField(User, on_delete=models.CASCADE)  
    ROLE_CHOICES = (  
        ('user', 'User'),  
        ('driver', 'Driver'),  
        ('admin', 'Admin'),  
    )  
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='user')  

    def __str__(self):  
        return self.user.username  

# Driver Model
class Driver(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    license_number = models.CharField(max_length=50, unique=True)
    phone_number = models.CharField(max_length=15, unique=True)

    def __str__(self):
        return f"{self.user.username} - {self.license_number}"

# Car Model
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
    price_per_hour = models.DecimalField(max_digits=10, decimal_places=2, help_text="Price per hour in USD")
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

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    car = models.ForeignKey(Car, on_delete=models.CASCADE)
    driver = models.ForeignKey(Driver, on_delete=models.SET_NULL, null=True, blank=True)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    total_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def save(self, *args, **kwargs):
        """ Calculate the total cost based on the reservation duration. """
        if self.start_date and self.end_date:
            duration = self.end_date - self.start_date
            hours = duration.total_seconds() / 3600  # Convert seconds to hours
            
            # Charge per day if duration is at least 24 hours
            if duration >= timedelta(days=1):
                days = duration.days + (duration.seconds / 86400)  # Convert remaining seconds to fraction of a day
                self.total_cost = round(days * self.car.price_per_day, 2)
            else:
                self.total_cost = round(hours * self.car.price_per_hour, 2)

        super().save(*args, **kwargs)

    def __str__(self):
        return f"Reservation {self.id} - {self.car} by {self.user.username} (${self.total_cost})"
