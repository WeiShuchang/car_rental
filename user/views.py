from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from administrator.models import Car

# Create your views here.
def user_dashboard(request):
    return render(request, "user/user_dashboard.html")

def cars_for_rent(request):
    cars_list = Car.objects.filter(available=True)  # Fetch only available cars
    paginator = Paginator(cars_list, 5)  # Show 5 cars per page

    page_number = request.GET.get("page")
    cars = paginator.get_page(page_number)

    return render(request, "user/cars_for_rent.html", {"cars": cars})

def car_detail(request, plate_number):
    car = get_object_or_404(Car, plate_number=plate_number)
    return render(request, 'user/car_detail.html', {'car': car})