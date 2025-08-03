from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.csrf import csrf_protect
from . models import Driver, Reservation, ChatRoom
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.utils import timezone

def admin_dashboard(request):
    reservation_counts = {
        'pending': Reservation.objects.filter(status='pending').count(),
        'approved': Reservation.objects.filter(status='approved').count(),
        'cancelled': Reservation.objects.filter(status='cancelled').count(),
        'completed': Reservation.objects.filter(status='completed').count(),
    }

    return render(request, "administrator/admin_dashboard.html", {
        'reservation_counts': reservation_counts
    })

def pending_reservations(request):
    reservations = Reservation.objects.filter(status='pending').select_related('car', 'user').order_by('-start_date')
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

        # Create chat room for this reservation if it doesn't exist
        if not hasattr(reservation, 'chat_room'):
            ChatRoom.objects.create(reservation=reservation)

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
        # Check if reservation is already completed
        if reservation.status == 'completed':
            messages.warning(request, "This reservation is already completed.")
            return redirect('approved_reservations')  # Or your appropriate redirect
        
        # Validate that reservation is in an approvable state
        if reservation.status != 'approved':
            messages.error(request, "Only approved reservations can be marked as completed.")
            return redirect('approved_reservations')
            
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
    
    return redirect('approved_reservations')  # Adjust to your actual URL name

@login_required

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

