
from administrator.models import Reservation

def driver_reservation_counts(request):
    if request.user.is_authenticated and hasattr(request.user, 'driver'):
        counts = {
            'approved_count': Reservation.objects.filter(
                driver=request.user.driver,
                status='approved'
            ).count(),
            'completed_count': Reservation.objects.filter(
                driver=request.user.driver,
                status='completed'
            ).count(),
        }
        return counts
    return {}