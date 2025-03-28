from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from administrator.forms import CarForm, DriverForm, SignUpForm
from django.contrib import messages
from administrator.models import UserProfile, Car

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
