from django.shortcuts import render, get_object_or_404
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from .models import Car
from .forms import CarForm
from django.core.paginator import Paginator
from django.http import JsonResponse

def admin_dashboard(request):
    return render(request, "administrator/admin_dashboard.html")

def car_list(request):
    cars_list = Car.objects.all().order_by('-id')
    paginator = Paginator(cars_list, 10)  # Show 10 cars per page
    page_number = request.GET.get('page')
    cars = paginator.get_page(page_number)

    context = {
        'cars': cars,
    }
    return render(request, 'administrator/car_list.html', context)

@csrf_exempt

def add_car(request):
    if request.method == 'POST':
        form = CarForm(request.POST, request.FILES)
        if form.is_valid():
            car = form.save()
            return JsonResponse({
                'status': 'success',
                'message': 'Car added successfully!',
                'car': {
                    'id': car.id,
                    'brand': car.brand,
                    'model': car.model,
                    'year': car.year,
                    'plate_number': car.plate_number,
                    'body_type': car.body_type,
                    'price_per_hour': car.price_per_hour,
                    'price_per_day': car.price_per_day,
                    'available': car.available,
                },
                'image_url': car.image.url if car.image else ''
            })
        else:
            return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)

    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)

@csrf_protect
def delete_car(request):
    if request.method == "POST":
        car_id = request.POST.get("id")
        car = get_object_or_404(Car, id=car_id)
        car.delete()
        return JsonResponse({"status": "success", "message": "Car deleted successfully"})
    
    return JsonResponse({"status": "error", "message": "Invalid request"}, status=400)