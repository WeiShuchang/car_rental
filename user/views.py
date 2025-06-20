from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from administrator.models import Car, Reservation
from django.contrib.auth.decorators import login_required
from django.utils.dateparse import parse_datetime
from django.contrib import messages
from django.utils.timezone import make_aware
from datetime import timedelta
from django.http import JsonResponse
from django.views.decorators.http import require_POST

# Create your views here.
def user_dashboard(request):
    cars = Car.objects.filter(available=True)  # Fetch only available cars
    return render(request, "user/user_dashboard.html", {"cars": cars})

def cars_for_rent(request):
    cars_list = Car.objects.filter(available=True)  # Fetch only available cars
    paginator = Paginator(cars_list, 5)  # Show 5 cars per page

    page_number = request.GET.get("page")
    cars = paginator.get_page(page_number)

    return render(request, "user/cars_for_rent.html", {"cars": cars})

def car_detail(request, plate_number):
    car = get_object_or_404(Car, plate_number=plate_number)
    return render(request, 'user/car_detail.html', {'car': car})


@login_required
def rent_car(request, plate_number):
    car = get_object_or_404(Car, plate_number=plate_number)

    if request.method == "POST":
        # pull raw strings
        start_str = request.POST.get("start_date")
        end_str   = request.POST.get("end_date")
        payment   = request.POST.get("payment_method")

        # convert → aware datetimes
        start_dt = make_aware(parse_datetime(start_str)) if start_str else None
        end_dt   = make_aware(parse_datetime(end_str))   if end_str   else None

        if not start_dt or not end_dt:
            messages.error(request, "Please select valid start and end dates.")
            return redirect("car_detail", plate_number=plate_number)

        if start_dt >= end_dt:
            messages.error(request, "End date must be after start date.")
            return redirect("car_detail", plate_number=plate_number)

        # ---- rental‑day logic --------------------------------------------
        # Compare only the calendar dates, not the hours/minutes.
        day_diff = (end_dt.date() - start_dt.date()).days
        rental_days = day_diff or 1          # at least one day
        # -------------------------------------------------------------------

        total_cost = rental_days * car.price_per_day

        Reservation.objects.create(
            user=request.user,
            car=car,
            start_date=start_dt,
            end_date=end_dt,
            payment_method=payment,
            total_cost=total_cost,
            # rental_days=rental_days,        # ↯ keep if you have this field
        )

        messages.success(
            request,
            f"Car reserved successfully! "
            f"Please wait for the administrator to approve the reservation. "
            f"Total cost: ₱{total_cost:,.2f}"
        )
        return redirect("user_pending_reservations")

    # GET fallback
    return redirect("car_detail", plate_number=plate_number)

@login_required
def pending_reservations(request):
    reservations = Reservation.objects.filter(user=request.user, status='pending').order_by('-start_date')
    return render(request, 'user/pending_reservations.html', {'reservations': reservations})

@login_required
@require_POST
def cancel_reservation(request):
    reservation_id = request.POST.get('reservation_id')
    reason = request.POST.get('reason_for_cancelling')
    
    try:
        reservation = Reservation.objects.get(id=reservation_id, user=request.user)
        
        if reservation.status == 'cancelled':
            messages.error(request, 'Reservation is already cancelled')
            return redirect('user_pending_reservations')  # Replace with your actual view/url name
        
        reservation.status = 'cancelled'
        reservation.reason_for_cancelling = reason
        reservation.cancelled_by = 'user'
        reservation.save()
        
        messages.success(request, 'Reservation cancelled successfully')
        return redirect('user_pending_reservations')  # Replace with your actual view/url name
    
    except Reservation.DoesNotExist:
        messages.error(request, 'Reservation not found')
        return redirect('user_pending_reservations')  # Replace with your actual view/url name
    except Exception as e:
        messages.error(request, f'Error cancelling reservation: {str(e)}')
        return redirect('user_pending_reservations')  # Replace with your actual view/url name
    
@login_required
def approved_reservations(request):
    reservations = Reservation.objects.filter(status='approved', user=request.user).order_by("-id")
    return render(request, 'user/approved_reservations.html', {'reservations': reservations})

@login_required
def cancelled_reservations_view(request):
    cancelled_reservations = Reservation.objects.filter(user=request.user, status='cancelled').order_by("-id")
    context = {
        'reservations': cancelled_reservations,
    }
    return render(request, 'user/cancelled_reservations.html', context)

@login_required
def reservation_history(request):
    # Get all reservations for the current user, ordered by start_date (newest first)
    reservations = Reservation.objects.filter(user=request.user).order_by('-start_date')
    
    context = {
        'reservations': reservations,
    }
    return render(request, 'user/history.html', context)