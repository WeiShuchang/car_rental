from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from .models import Car, Driver
from .forms import CarForm, DriverForm, SignUpForm
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate, logout
from django.shortcuts import render, redirect
from .models import UserProfile

def admin_dashboard(request):
    driver_count = Driver.objects.count()
    car_count = Car.objects.count()
    
    context = {
        'driver_count': driver_count,
        'car_count': car_count,
    }
    
    return render(request, "administrator/admin_dashboard.html", context)

def car_list(request):
    cars_list = Car.objects.all().order_by('-id')
    paginator = Paginator(cars_list, 10)  # Show 10 cars per page
    page_number = request.GET.get('page')
    cars = paginator.get_page(page_number)

    context = {
        'cars': cars,
    }
    return render(request, 'administrator/car_list.html', context)
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


def signup_view(request):
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # Log in the user after signing up
            messages.success(request, "Signup successful! Welcome to your dashboard.")
            return redirect('user_dashboard')  # Redirect to user dashboard
        else:
            messages.error(request, "Signup failed. Please check the form for errors.")
    else:
        form = SignUpForm()
    
    return render(request, 'authentication/signup_page.html', {'form': form})
def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, "You have successfully logged in.")
            
            # Get the user profile and check the role
            try:
                user_profile = UserProfile.objects.get(user=user)
                if user_profile.role == "admin":
                    return redirect("admin_dashboard")
                elif user_profile.role == "user":
                    return redirect("user_dashboard")
                elif user_profile.role == "driver":
                    return redirect("driver_dashboard")  # If you have a separate driver dashboard
            except UserProfile.DoesNotExist:
                messages.error(request, "User profile not found.")
                return redirect("login")  # Redirect back to login if no profile found

        else:
            messages.error(request, "Invalid username or password. Please try again.")

    return render(request, "authentication/login_page.html")

def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect("login")  # Redirect to the login page