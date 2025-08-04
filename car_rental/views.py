from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from administrator.forms import CarForm, DriverForm, SignUpForm
from django.contrib import messages
from administrator.models import UserProfile, Car, ChatRoom, Message
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST
from django.contrib.auth.models import User

def homepage(request):
    featured_cars = Car.objects.filter(available=True)[:6]  # Fetch only available cars, limit to 6
    return render(request, "home/homepage.html", {'cars': featured_cars})  # Pass as 'cars' to match template

def signup_view(request):
    if request.method == "POST":
        form = SignUpForm(request.POST)  # Only one instance needed
        if form.is_valid():
            user = form.save()  # This will send the email automatically
            messages.success(request, "Registration successful! Please check your email to confirm your account.")
            return redirect('login')
        else:
            print(form.errors)  # Debugging: Check form errors in console
            messages.error(request, "Signup failed. Please check the form.")
    else:
        form = SignUpForm()
    
    return render(request, 'authentication/signup_page.html', {'form': form})




def confirm_email_view(request, token):
    profile = get_object_or_404(UserProfile, email_confirmation_token=token)
    if not profile.is_email_confirmed:
        profile.is_email_confirmed = True
        profile.email_confirmation_token = None  # Clear the token after use
        profile.save()
        profile.user.is_active = True  # Activate the user
        profile.user.save()
        messages.success(request, "Email confirmed successfully! You can now login.")
    else:
        messages.info(request, "Email already confirmed.")
    
    return redirect('login')

def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)

        if user is not None:
            try:
                
                login(request, user)
                user_profile = UserProfile.objects.get(user=user)
                
                # Check if email is verified
                if not user_profile.is_email_verified:
                    messages.warning(request, "Please verify your email first!")
                    return redirect('verify-email')  # Redirect to verification page
                
           
                messages.success(request, "You have successfully logged in.")
                
                # Redirect based on role
                if user_profile.role == "admin":
                    return redirect("admin_dashboard")
                elif user_profile.role == "user":
                    return redirect("user_dashboard")
                elif user_profile.role == "driver":
                    return redirect("driver_dashboard")
                elif user_profile.role == "superadmin":
                    return redirect("superadmin_dashboard")
                    
            except UserProfile.DoesNotExist:
                messages.error(request, "User profile not found.")
                return redirect("login")

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