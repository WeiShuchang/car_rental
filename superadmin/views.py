from django.shortcuts import render, redirect
from administrator.models import Car, Driver, Reservation, UserProfile, ChatRoom, CarImage
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
from django.utils import timezone
from django.http import HttpResponse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle, Paragraph, Spacer,SimpleDocTemplate
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from io import BytesIO
from django.utils import timezone
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from django.db.models import Q

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
    # Get search and filter parameters from request
    search_query = request.GET.get('q', '')
    status_filter = request.GET.get('status', '')
    payment_filter = request.GET.get('payment', '')
    
    # Start with base queryset
    reservations_list = Reservation.objects.all().select_related(
        'user', 'car', 'driver', 'driver__user'
    ).order_by('-created_at')
    
    # Apply search filter if provided
    if search_query:
        reservations_list = reservations_list.filter(
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(car__model__icontains=search_query) |
            Q(car__plate_number__icontains=search_query) |
            Q(id__icontains=search_query)
        )
    
    # Apply status filter if provided
    if status_filter:
        reservations_list = reservations_list.filter(status=status_filter)
    
    # Apply payment status filter if provided
    if payment_filter:
        reservations_list = reservations_list.filter(payment_status=payment_filter)
    
    # Pagination (25 items per page)
    paginator = Paginator(reservations_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'reservations': page_obj.object_list,
        'search_query': search_query,
        'status_filter': status_filter,
        'payment_filter': payment_filter,
        'status_choices': Reservation.STATUS_CHOICES,
        'payment_choices': Reservation.PAYMENT_STATUS_CHOICES,
    }
    
    return render(request, 'administrator/all_reservations.html', context)

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
    cars = Car.objects.all()

    if request.method == 'POST':
        form = CarForm(request.POST)
        if form.is_valid():
            try:
                # Get all uploaded images
                uploaded_images = request.FILES.getlist('images')
                
                if not uploaded_images:
                    messages.error(request, "At least one image is required.")
                    return render(request, 'administrator/car_list.html', {'form': form, 'cars': cars})
                
                # Set the first image as the main car image
                car = form.save(commit=False)
                car.image = uploaded_images[0]  # First image is the main one
                car.save()
                
                # Save remaining images as CarImage instances
                for image in uploaded_images[1:]:
                    CarImage.objects.create(car=car, image=image)
                
                messages.success(
                    request, 
                    f"Car '{car.brand} {car.model}' added successfully!"
                )
                return redirect('car_list')
            except Exception as e:
                messages.error(request, f"An error occurred: {str(e)}")
        else:
            messages.error(request, "Please correct the errors below.")

        return render(request, 'administrator/car_list.html', {
            'form': form,
            'cars': cars
        })
    else:
        form = CarForm()

    return render(request, 'administrator/car_list.html', {
        'form': form, 
        'cars': cars
    })

@csrf_protect
def delete_car(request, car_id):
    car = get_object_or_404(Car, id=car_id)
    car.delete()
    messages.success(request, "Car deleted successfully.")
    return redirect("car_list")  # Change this to your actual view name


def edit_car(request, car_id):
    car = get_object_or_404(Car, id=car_id)
    
    if request.method == "GET":
        # Get all images (main + additional)
        images = []
        if car.image:
            images.append({
                'url': car.image.url,
                'is_main': True,
                'id': 'main'
            })
        
        for img in car.images.all():
            images.append({
                'url': img.image.url,
                'is_main': False,
                'id': img.id
            })
        
        return JsonResponse({
            "id": car.id,
            "brand": car.brand,
            "model": car.model,
            "year": car.year,
            "plate_number": car.plate_number,
            "body_type": car.body_type,
            "available": car.available,
            "price_per_day": str(car.price_per_day),
            "seating_capacity": car.seating_capacity,
            "images": images,
            "main_image_url": car.image.url if car.image else None
        })

    elif request.method == "POST":
        form = CarForm(request.POST, request.FILES, instance=car)
        if form.is_valid():
            # Handle main image update
            if 'image' in request.FILES:
                car.image = request.FILES['image']
            
            # Handle additional images
            if 'additional_images' in request.FILES:
                for img in request.FILES.getlist('additional_images'):
                    CarImage.objects.create(car=car, image=img)
            
            # Handle image deletions
            if 'delete_images' in request.POST:
                deleted_ids = request.POST.getlist('delete_images')
                CarImage.objects.filter(id__in=deleted_ids).delete()
            
            if 'delete_main_image' in request.POST:
                car.image.delete()
                car.image = None
            
            form.save()
            messages.success(request, "Car details updated successfully!")
            return redirect("car_list")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
            return redirect("car_list")


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

    return render(request, 'superadmin/pending_reservations.html', {
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
            return redirect("superadmin_pending_reservations")

        # Validate driver
        if driver_id:
            driver = Driver.objects.filter(id=driver_id, availability=True).first()
            if not driver:
                messages.error(request, "Invalid driver selection or driver is unavailable.")
                return redirect("superadmin_pending_reservations")

            # Assign driver & update availability
            reservation.driver = driver
            driver.save()

        # Approve reservation
        reservation.status = "approved"
        reservation.save()

        # Create chat room for this reservation if it doesn't exist
        if not hasattr(reservation, 'chat_room'):
            ChatRoom.objects.create(reservation=reservation)

        messages.success(request, "Reservation approved successfully!")
        return redirect("superadmin_pending_reservations")

    messages.error(request, "Invalid request method.")
    return redirect("superadmin_pending_reservations")


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

    return redirect("superadmin_pending_reservations")

def approved_reservations(request):
    reservations = Reservation.objects.filter(status='approved').select_related('user', 'car', 'driver').order_by("-id")
    return render(request, 'superadmin/approved_reservations.html', {'reservations': reservations})

def cancelled_reservations(request):
    reservations = Reservation.objects.filter(status='cancelled').select_related('user', 'car', 'driver').order_by("-id")
    return render(request, 'superadmin/cancelled_reservations.html', {'reservations': reservations})


def complete_reservation(request, reservation_id):
    reservation = get_object_or_404(Reservation, id=reservation_id)
    
    if request.method == "POST":
        # Check if reservation is already completed
        if reservation.status == 'completed':
            messages.warning(request, "This reservation is already completed.")
            return redirect('superadmin_approved_reservations')  # Or your appropriate redirect
        
        # Validate that reservation is in an approvable state
        if reservation.status != 'approved':
            messages.error(request, "Only approved reservations can be marked as completed.")
            return redirect('superadmin_approved_reservations')
            
        try:
            # Update reservation status and set completion timestamp
            reservation.status = 'completed'
            reservation.date_completed = timezone.now()
            
            # Free up the driver if one was assigned
            if reservation.driver:
                reservation.driver.availability = True
                reservation.driver.save()
                
            reservation.save()
            
            messages.success(request, f"Reservation #{reservation.id} successfully marked as completed.")
        except Exception as e:
            messages.error(request, f"Error completing reservation: {str(e)}")
            # Consider logging the error here as well
    
    return redirect('superadmin_approved_reservations')  # Adjust to your actual URL name

@login_required
def completed_reservations(request):
    reservations = Reservation.objects.filter(status='completed').order_by('-end_date')
    
    context = {
        'reservations': reservations,
    }
    return render(request, 'superadmin/completed_reservations.html', context)

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
            
    return redirect('superadmin_pending_reservations')  # Replace with your actual redirect target

def generate_reservations_pdf(request):
    # Get search and filter parameters
    search_query = request.GET.get('q', '')
    status_filter = request.GET.get('status', '')
    payment_filter = request.GET.get('payment', '')

    # Get filtered reservations
    reservations = Reservation.objects.all().select_related(
        'user', 'car', 'driver', 'driver__user'
    ).order_by('-created_at')

    if search_query:
        reservations = reservations.filter(
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(car__model__icontains=search_query) |
            Q(car__plate_number__icontains=search_query)
        )

    if status_filter:
        reservations = reservations.filter(status=status_filter)

    if payment_filter:
        reservations = reservations.filter(payment_status=payment_filter)

    # Create PDF response
    response = HttpResponse(content_type='application/pdf')
    filename = f"reservations_report_{timezone.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(letter),
                         leftMargin=0.5*inch,
                         rightMargin=0.5*inch,
                         topMargin=0.5*inch,
                         bottomMargin=0.5*inch)

    elements = []
    styles = getSampleStyleSheet()

    # Title with filters
    title_text = "Ashley's Car Rental - Reservations Report"
    filter_info = []
    
    if search_query:
        filter_info.append(f"Search: {search_query}")
    if status_filter:
        status_display = dict(Reservation.STATUS_CHOICES).get(status_filter, status_filter)
        filter_info.append(f"Status: {status_display}")
    if payment_filter:
        payment_display = dict(Reservation.PAYMENT_STATUS_CHOICES).get(payment_filter, payment_filter)
        filter_info.append(f"Payment: {payment_display}")

    # Add title and filters
    elements.append(Paragraph(title_text, styles['Heading1']))
    if filter_info:
        elements.append(Paragraph("<br/>".join(filter_info), styles['Normal']))
    elements.append(Paragraph(f"Generated on: {timezone.now().strftime('%B %d, %Y at %I:%M %p')}", styles['Normal']))
    elements.append(Spacer(1, 0.3*inch))

    # Table data with removed contact column and PHP instead of ₱
    table_data = [
        ["ID", "Customer", "Car Model", "Plate #", 
         "Reservation Dates", "Days", "Status", "Payment", "Total (PHP)"]
    ]

    for reservation in reservations:        
        table_data.append([
            str(reservation.id),
            reservation.user.get_full_name() or reservation.user.username,
            reservation.car.model,
            reservation.car.plate_number,
            f"{reservation.start_date.strftime('%b %d, %Y')} to {reservation.end_date.strftime('%b %d, %Y')}",
            str((reservation.end_date - reservation.start_date).days + 1),
            reservation.get_status_display(),
            f"{reservation.get_payment_status_display()} ({reservation.get_payment_method_display()})",
            "PHP {:,.2f}".format(reservation.total_cost)  # Changed to PHP
        ])

    # Create table with adjusted column widths
    col_widths = [
        0.5*inch,   # ID
        1.5*inch,   # Customer
        1.8*inch,   # Car Model
        0.8*inch,   # Plate #
        1.8*inch,   # Dates
        0.5*inch,   # Days
        0.8*inch,   # Status
        1.2*inch,   # Payment
        1.0*inch    # Total
    ]
    
    table = Table(table_data, colWidths=col_widths, repeatRows=1)
    
    # Table style
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#343a40')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 9),
        ('BOTTOMPADDING', (0,0), (-1,0), 8),
        ('BACKGROUND', (0,1), (-1,-1), colors.HexColor('#f8f9fa')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#dee2e6')),
        ('FONTSIZE', (0,1), (-1,-1), 8),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))

    elements.append(table)
    elements.append(Spacer(1, 0.3*inch))

    # Summary section with PHP
    total_revenue = sum(r.total_cost for r in reservations)
    summary_text = f"""
    <b>SUMMARY</b><br/>
    Total Reservations: {len(reservations)}<br/>
    Total Revenue: PHP {total_revenue:,.2f}<br/>
    Generated by: {request.user.get_full_name() or request.user.username}
    """
    elements.append(Paragraph(summary_text, styles['Normal']))

    # Build PDF
    doc.build(elements)

    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)
    return response

def edit_user(request, user_id):
    if not request.user.is_authenticated or not request.user.userprofile.role in ['admin', 'superadmin']:
        return redirect('login')  # or wherever you want to redirect unauthorized users
    
    user = get_object_or_404(User, id=user_id)
    profile = get_object_or_404(UserProfile, user=user)
    
    if request.method == 'POST':
        # Update user fields
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.email = request.POST.get('email', '')
        user.save()
        
        # Update profile fields
        profile.contact_number = request.POST.get('contact_number', '')
        profile.save()
        
        messages.success(request, 'User updated successfully!')
        return redirect('all_users_list')  # redirect to your user management page
    
    # If not POST, redirect back (this shouldn't happen as form is in modal)
    return redirect('all_users_list')

def toggle_user_status(request, user_id):
    if not request.user.is_authenticated or not request.user.userprofile.role in ['admin', 'superadmin']:
        return redirect('login')  # Redirect unauthorized users
    
    user = get_object_or_404(User, id=user_id)
    
    # Toggle the active status
    user.is_active = not user.is_active
    user.save()
    
    # Set appropriate message
    if user.is_active:
        messages.success(request, f'User {user.username} has been activated successfully!')
    else:
        messages.success(request, f'User {user.username} has been deactivated successfully!')
    
    return redirect('all_users_list')  # Redirect back to user management page

def edit_admin(request, user_id):
    if not request.user.is_authenticated or request.user.userprofile.role != 'superadmin':
        messages.error(request, "You don't have permission to perform this action.")
        return redirect('admin_dashboard')  # or your admin dashboard URL
    
    user = get_object_or_404(User, id=user_id)
    profile = get_object_or_404(UserProfile, user=user)
    
    # Update user fields
    user.first_name = request.POST.get('first_name', '')
    user.last_name = request.POST.get('last_name', '')
    user.email = request.POST.get('email', '')
    user.save()
    
    # Update profile fields
    profile.contact_number = request.POST.get('contact_number', '')
    profile.role = request.POST.get('role', 'admin')  # Default to admin if not specified
    profile.save()
    
    messages.success(request, 'Admin updated successfully!')
    return redirect('all_admins_list')  # redirect to your admin management page


def toggle_admin_status(request, user_id):
    if not request.user.is_authenticated or request.user.userprofile.role != 'superadmin':
        messages.error(request, "You don't have permission to perform this action.")
        return redirect('admin_dashboard')
    
    user = get_object_or_404(User, id=user_id)
    
    # Toggle the active status
    user.is_active = not user.is_active
    user.save()
    
    if user.is_active:
        messages.success(request, f'Admin {user.username} has been restored successfully!')
    else:
        messages.success(request, f'Admin {user.username} has been revoked successfully!')
    
    return redirect('all_admins_list')