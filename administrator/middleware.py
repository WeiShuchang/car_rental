from django.shortcuts import redirect
from .models import UserProfile
from django.utils.deprecation import MiddlewareMixin

class RoleBasedAccessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        # Skip middleware for these URLs
        if request.path.startswith('/static/') or request.path.startswith('/media/') or request.path.startswith('/admin/'):
            return None
        
        open_urls = [
           
            'signup/',
            'login/',
            'adminlogin/',
            'driverlogin/',
            'logout/',
            'logout-admin/',
            'driverlogout/',
        ]
        
        if any(request.path_info.lstrip('/').startswith(url) for url in open_urls):
            return None
        
        if not request.user.is_authenticated:
            return None  # Let other middleware handle unauthorized users
        
        try:
            profile = UserProfile.objects.get(user=request.user)
            role = profile.role
        except UserProfile.DoesNotExist:
            return redirect('homepage')
        
        # Define allowed URL prefixes for each role
        role_urls = {
            'superadmin': 'superadmin/',
            'admin': 'administrator/',
            'user': 'user/',
            'driver': 'driver/',
        }
        
        # Check if the current path starts with the allowed prefix for the user's role
        if not request.path_info.lstrip('/').startswith(role_urls.get(role, '')):
            # Redirect to appropriate dashboard
            if role == 'superadmin':
                return redirect('superadmin_dashboard')
            elif role == 'admin':
                return redirect('admin_dashboard')
            elif role == 'driver':
                return redirect('driver_dashboard')
            elif role == 'user':
                return redirect('user_dashboard')
        
        return None

class UnauthorizedUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_view(self, request, view_func, view_args, view_kwargs):
        # Skip static/media files
        if request.path.startswith(('/static/', '/media/', '/staticfiles/')):
            return None

        # Allow homepage, signup, and login pages
        allowed_urls = ['/', '/signup/', '/login/', '/adminlogin/', '/driverlogin/']
        if request.path in allowed_urls:
            return None

        # Redirect to homepage if not logged in
        if not request.user.is_authenticated:
            return redirect('/')  # Sends them back to homepage (no loop)

        return None

class AuthorizedUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_view(self, request, view_func, view_args, view_kwargs):
        # Skip static/media files
        if request.path.startswith(('/static/', '/media/')):
            return None

        # Skip if not logged in
        if not request.user.is_authenticated:
            return None

        # If accessing homepage, redirect to dashboard
        if request.path == '/':
            try:
                profile = UserProfile.objects.get(user=request.user)
                if profile.role == 'superadmin':
                    return redirect('superadmin_dashboard')
                elif profile.role == 'admin':
                    return redirect('admin_dashboard')
                elif profile.role == 'driver':
                    return redirect('driver_dashboard')
                elif profile.role == 'user':
                    return redirect('user_dashboard')
            except UserProfile.DoesNotExist:
                pass  # Don't redirect if no profile exists

        return None  # Allow other pages
    
class PreventBackHistoryMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        """
        Add headers to prevent browser caching and enable no-store behavior,
        similar to Laravel's middleware.
        """
        response['Cache-Control'] = 'no-cache, no-store, max-age=0, must-revalidate'
        response['Pragma'] = 'no-cache'
        response['Expires'] = 'Sat, 26 Jul 1997 05:00:00 GMT'  # Expire in the past

        return response


