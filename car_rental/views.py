from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from administrator.forms import CarForm, DriverForm, SignUpForm
from django.contrib import messages
from administrator.models import UserProfile, Car, ChatRoom, Message
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST


def homepage(request):
    featured_cars = Car.objects.filter(available=True)[:6]  # Fetch only available cars, limit to 6
    return render(request, "home/homepage.html", {'cars': featured_cars})  # Pass as 'cars' to match template

def signup_view(request):
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Signup successful!")
            return redirect('user_dashboard')
        else:
            # Add this for debugging:
            print(form.errors)  # Check console for errors
            messages.error(request, "Signup failed. Please check the form.")
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
                elif user_profile.role == "superadmin":
                    return redirect("superadmin_dashboard")  # If you have a separate driver dashboard
                
            except UserProfile.DoesNotExist:
                messages.error(request, "User profile not found.")
                return redirect("login")  # Redirect back to login if no profile found

        else:
            messages.error(request, "Invalid username or password. Please try again.")

    return render(request, "authentication/login_page.html")

def adminlogin_view(request):
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
                elif user_profile.role == "superadmin":
                    return redirect("superadmin_dashboard")  # If you have a separate driver dashboard
            except UserProfile.DoesNotExist:
                messages.error(request, "User profile not found.")
                return redirect("admin_login")  # Redirect back to login if no profile found

        else:
            messages.error(request, "Invalid username or password. Please try again.")

    return render(request, "authentication/adminlogin_page.html")

def driverlogin_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, "You have successfully logged in.")

            try:
                user_profile = UserProfile.objects.get(user=user)
                if user_profile.role == "driver":
                    return redirect("driver_dashboard")
                else:
                    messages.error(request, "Access denied: This login is for drivers only.")
                    return redirect("driver_login")
            except UserProfile.DoesNotExist:
                messages.error(request, "User profile not found.")
                return redirect("driver_login")
        else:
            messages.error(request, "Invalid username or password. Please try again.")

    return render(request, "authentication/driverlogin_page.html")

def adminlogout_view(request):
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect("admin_login")  # Redirect to the login page

def driverlogout_view(request):
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect("driver_login")  # Redirect to the login page

def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect("login")  # Redirect to the login page

@require_GET
def chat_messages(request):
    room_id = request.GET.get('room_id')
    if not room_id:
        return JsonResponse({'error': 'Room ID required'}, status=400)
    
    try:
        room = ChatRoom.objects.get(id=room_id, reservation__driver__user=request.user)
        messages = room.messages.all().order_by('timestamp')
        
        messages_data = [{
            'id': msg.id,
            'content': msg.content,
            'timestamp': msg.timestamp.strftime("%H:%M"),
            'is_sender': msg.sender == request.user,
        } for msg in messages]
        
        return JsonResponse({'messages': messages_data})
    
    except ChatRoom.DoesNotExist:
        return JsonResponse({'error': 'Chat room not found'}, status=404)

@require_POST
def send_chat_message(request):
    room_id = request.POST.get('room_id')
    content = request.POST.get('content')
    
    if not room_id or not content:
        return JsonResponse({'error': 'Room ID and content required'}, status=400)
    
    try:
        room = ChatRoom.objects.get(id=room_id, reservation__driver__user=request.user)
        message = Message.objects.create(
            chat_room=room,
            sender=request.user,
            content=content
        )
        
        return JsonResponse({
            'success': True,
            'message': {
                'id': message.id,
                'content': message.content,
                'timestamp': message.timestamp.strftime("%H:%M"),
            }
        })
    
    except ChatRoom.DoesNotExist:
        return JsonResponse({'error': 'Chat room not found'}, status=404)