from django.shortcuts import render, redirect
from administrator.models import Car, Driver, Reservation, UserProfile
from administrator.forms import CarForm
from django.db.models import Count
from django.contrib import messages
from django.core.paginator import Paginator
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_protect
# Create your views here.

def superadmin_dashboard(request):
    # Existing counts
    reservation_count = Reservation.objects.count()
    user_count = UserProfile.objects.filter(role='user').count()
    admin_count = UserProfile.objects.filter(role='admin').count()
    driver_count = Driver.objects.count()
    car_count = Car.objects.count()
    
    # Get reservation status counts
    status_counts = Reservation.objects.values('status').annotate(count=Count('status')).order_by('status')
    
    # Prepare data for chart
    status_data = {
        'labels': [choice[1] for choice in Reservation.STATUS_CHOICES],
        'data': [0] * len(Reservation.STATUS_CHOICES)
    }
    
    for item in status_counts:
        index = [choice[0] for choice in Reservation.STATUS_CHOICES].index(item['status'])
        status_data['data'][index] = item['count']
    
    context = {
        'reservation_count': reservation_count,
        'user_count': user_count,
        'admin_count': admin_count,
        'driver_count': driver_count,
        'car_count': car_count,
        'status_data': status_data,  # Add this line
    }
    
    return render(request, "administrator/superadmin_dashboard.html", context)

def car_list(request):
    cars_list = Car.objects.all().order_by('-id')
    paginator = Paginator(cars_list, 10)  # Show 10 cars per page
    page_number = request.GET.get('page')
    cars = paginator.get_page(page_number)

    context = {
        'cars': cars,
    }
    return render(request, 'administrator/car_list.html', context)


def all_users_list(request):
    users = UserProfile.objects.filter(role='user').select_related('user')
    return render(request, 'administrator/all_users_list.html', {'users': users})


def all_admins_list(request):
    admins = UserProfile.objects.filter(role='admin').select_related('user')
    return render(request, 'administrator/all_admins_list.html', {'admins': admins})

@login_required
def all_reservations(request):
    reservations_list = Reservation.objects.all().select_related(
        'user', 'car', 'driver', 'driver__user'
    ).order_by('-created_at')
    
    paginator = Paginator(reservations_list, 10)  # Show 10 reservations per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'administrator/all_reservations.html', {
        'page_obj': page_obj,
        'reservations': page_obj.object_list  # Add this line
    })
def add_admin(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        contact_number = request.POST.get('contact_number')

        # Validate required fields
        if not all([username, email, password]):
            messages.error(request, 'Username, email and password are required')
            return redirect('all_admins_list')

        try:
            # Check if user already exists
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': email,
                    'password': make_password(password),
                    'first_name': first_name,
                    'last_name': last_name,
                    'is_staff': True
                }
            )
            
            if not created:
                messages.error(request, 'Username already exists')
                return redirect('all_admins_list')
            
            # Create or update user profile
            UserProfile.objects.update_or_create(
                user=user,
                defaults={
                    'role': 'admin',
                    'contact_number': contact_number
                }
            )
            
            messages.success(request, 'Admin user created successfully')
            return redirect('all_admins_list')
            
        except Exception as e:
            messages.error(request, f'Error creating admin: {str(e)}')
            return redirect('all_admins_list')
    
    return redirect('all_admins_list')


def add_car(request):
    cars = Car.objects.all()  # Fetch the list of cars

    if request.method == 'POST':
        form = CarForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                car = form.save()
                messages.success(request, f"Car '{car.brand} {car.model}' added successfully!")
                return redirect('car_list')  # Redirect to refresh the list after adding
            except Exception as e:
                error_message = f"An error occurred while saving the car: {e}"
        else:
            messages.error(request, f"An error occurred while saving the car, please try again")
            error_message = "Please correct the errors below."

        return render(request, 'administrator/car_list.html', {
            'form': form,
            'error_message': error_message,
            'cars': cars  # Ensure the car list is passed when an error occurs
        })
    else:
        form = CarForm()

    return render(request, 'administrator/car_list.html', {'form': form, 'cars': cars})

@csrf_protect
def delete_car(request, car_id):
    car = get_object_or_404(Car, id=car_id)
    car.delete()
    messages.success(request, "Car deleted successfully.")
    return redirect("car_list")  # Change this to your actual view name
def edit_car(request, car_id):
    car = get_object_or_404(Car, id=car_id)
    
    if request.method == "GET":
        # Return JSON data for the edit modal
        return JsonResponse({
            "id": car.id,
            "brand": car.brand,
            "model": car.model,
            "year": car.year,
            "plate_number": car.plate_number,
            "body_type": car.body_type,
            "price_per_hour": str(car.price_per_hour),
            "price_per_day": str(car.price_per_day),
        })

    elif request.method == "POST":
        form = CarForm(request.POST, request.FILES, instance=car)
        if form.is_valid():
            form.save()
            messages.success(request, "Car details updated successfully!")
            return redirect("car_list")  # Change this to your actual list view name
        else:
            # If the form is invalid, show error messages
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    
    return redirect("car_list")  # Redirect back to the car list page
def driver_list(request):
    drivers = Driver.objects.all()  # Fetch all drivers
    paginator = Paginator(drivers, 10)  # Show 10 drivers per page

    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, "administrator/driver_list.html", {
        "drivers": page_obj,  # Pass paginated drivers
        "page_obj": page_obj,  # Include page_obj for pagination controls
    })
def add_driver(request):
    drivers = Driver.objects.all()  # Fetch all drivers

    if request.method == "POST":
        first_name = request.POST["first_name"]
        last_name = request.POST["last_name"]
        username = request.POST["username"]
        email = request.POST["email"]
        password = request.POST["password"]
        confirm_password = request.POST["confirm_password"]
        license_number = request.POST["license_number"]
        phone_number = request.POST["phone_number"]
        image = request.FILES.get("image")  # Get uploaded image if provided

        # Validation checks
        if password != confirm_password:
            messages.error(request, "Passwords do not match!")
        elif User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists!")
        elif User.objects.filter(email=email).exists():
            messages.error(request, "Email already exists!")
        elif Driver.objects.filter(phone_number=phone_number).exists():
            messages.error(request, "Phone number already exists!")
        elif Driver.objects.filter(license_number=license_number).exists():
            messages.error(request, "License number already exists!")
        else:
            # Create User
            user = User.objects.create_user(
                username=username, email=email, password=password,
                first_name=first_name, last_name=last_name
            )
            user.save()

            # Assign driver role (if applicable)
            user_profile = user.userprofile
            user_profile.role = "driver"
            user_profile.save()

            # Create Driver with image
            driver = Driver.objects.create(
                user=user,
                license_number=license_number,
                phone_number=phone_number,
                image=image  # Save uploaded image
            )
            driver.save()

            messages.success(request, "Driver added successfully!")
            return redirect("driver_list")

        return render(request, "administrator/driver_list.html", {
            "drivers": drivers,
            "first_name": first_name,
            "last_name": last_name,
            "username": username,
            "email": email,
            "license_number": license_number,
            "phone_number": phone_number,
            "modal_open": True,
        })

    return redirect("driver_list")
def delete_driver(request, driver_id):
    driver = get_object_or_404(Driver, id=driver_id)
    driver.delete()
    messages.success(request, 'Driver deleted successfully.')
    return redirect('driver_list')  
def update_driver(request, driver_id):
    driver = get_object_or_404(Driver, id=driver_id)

    if request.method == "POST":
        username = request.POST.get("username")
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        email = request.POST.get("email")
        license_number = request.POST.get("license_number")
        phone_number = request.POST.get("phone_number")

        # Convert "true"/"false" string to boolean
        availability = request.POST.get("availability") == "true"

        # Update fields
        driver.user.username = username
        driver.user.first_name = first_name
        driver.user.last_name = last_name
        driver.user.email = email
        driver.license_number = license_number
        driver.phone_number = phone_number
        driver.availability = availability  # Update availability field

        if "driver_image" in request.FILES:
            driver.image = request.FILES["driver_image"]

        try:
            driver.user.save()
            driver.save()
            messages.success(request, "Driver details updated successfully!")
        except Exception as e:
            messages.error(request, f"Error updating driver: {e}")

        return redirect("driver_list")

    return render(request, "administrator/driver_list.html", {"driver": driver})
