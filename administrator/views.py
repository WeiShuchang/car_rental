from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from .models import Car, Driver, Reservation
from .forms import CarForm, DriverForm, SignUpForm
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.contrib import messages
from django.urls import reverse
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from django.shortcuts import render, redirect

from django.contrib.auth.decorators import login_required, user_passes_test

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


def pending_reservations(request):
    reservations = Reservation.objects.filter(status='pending').select_related('car', 'user')
    drivers = Driver.objects.filter(availability=True).select_related('user')  # Get only available drivers

    return render(request, 'administrator/pending_reservations.html', {
        'reservations': reservations,
        'drivers': drivers
    })

def approve_reservation(request, reservation_id):
    if request.method == "POST":
        driver_id = request.POST.get("driver")

        # Validate reservation
        reservation = get_object_or_404(Reservation, id=reservation_id)

        # Check if already approved
        if reservation.status == "approved":
            messages.warning(request, "This reservation has already been approved.")
            return redirect("pending_reservations")

        # Validate driver
        if driver_id:
            driver = Driver.objects.filter(id=driver_id, availability=True).first()
            if not driver:
                messages.error(request, "Invalid driver selection or driver is unavailable.")
                return redirect("pending_reservations")

            # Assign driver & update availability
            reservation.driver = driver
       
            driver.save()

        # Approve reservation
        reservation.status = "approved"
        reservation.save()

        messages.success(request, "Reservation approved successfully!")
        return redirect("pending_reservations")

    messages.error(request, "Invalid request method.")
    return redirect("pending_reservations")

def cancel_reservation(request):
    if request.method == "POST":
        print("Form submitted!")  # Debugging
        print("POST data:", request.POST)  # Debugging
        
        reservation_id = request.POST.get("reservation_id")
        reason = request.POST.get("reason_for_cancelling")
        cancelled_by = request.POST.get("cancelled_by")

        try:
            reservation = Reservation.objects.get(id=reservation_id)
            print("Found reservation:", reservation)  # Debugging
            
            if reservation.status == "pending":
                reservation.status = "cancelled"
                reservation.reason_for_cancelling = reason
                reservation.cancelled_by = cancelled_by
                reservation.is_cancelled_notif = True
                reservation.save()
                print("Reservation cancelled successfully")  # Debugging
                messages.success(request, "Reservation has been cancelled successfully.")
            else:
                messages.error(request, "This reservation cannot be cancelled.")
                
        except Reservation.DoesNotExist:
            messages.error(request, "Reservation not found.")
        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")
            print("Error:", str(e))  # Debugging

    return redirect("pending_reservations")

def approved_reservations(request):
    reservations = Reservation.objects.filter(status='approved').select_related('user', 'car', 'driver').order_by("-id")
    return render(request, 'administrator/approved_reservations.html', {'reservations': reservations})

def cancelled_reservations(request):
    reservations = Reservation.objects.filter(status='cancelled').select_related('user', 'car', 'driver').order_by("-id")
    return render(request, 'administrator/cancelled_reservations.html', {'reservations': reservations})

def complete_reservation(request, reservation_id):
    reservation = get_object_or_404(Reservation, id=reservation_id)
    
    if request.method == "POST":
        reservation.status = 'completed'
        reservation.save()
        messages.success(request, "Reservation marked as completed.")
    
    return redirect('approved_reservations')  # Adjust to your actual URL name

@login_required
@user_passes_test(lambda u: u.is_superuser)
def completed_reservations(request):
    reservations = Reservation.objects.filter(status='completed').order_by('-end_date')
    
    context = {
        'reservations': reservations,
    }
    return render(request, 'administrator/completed_reservations.html', context)
def update_payment_status(request, reservation_id):
    if request.method == 'POST':
        reservation = get_object_or_404(Reservation, id=reservation_id)
        new_status = request.POST.get('payment_status')
        
        # Validate the status
        if new_status in dict(Reservation.PAYMENT_STATUS_CHOICES).keys():
            reservation.payment_status = new_status
            reservation.save()
            messages.success(request, 'Payment status updated successfully!')
        else:
            messages.error(request, 'Invalid payment status selected.')
            
    return redirect('pending_reservations')  # Replace with your actual redirect target