"""
URL configuration for car_rental project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from . import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [

    path('superadmin/', include('superadmin.urls')),
    path('administrator/', include('administrator.urls')),
    path('user/', include('user.urls')),
    path('driver/', include('driver.urls')),

    path('admin/', admin.site.urls),

    #cannot be accessed when logged in:
    path('', views.homepage, name="homepage"), 
    path('signup/', views.signup_view, name='signup'), 
    path("login/", views.login_view, name="login"), 
    path("adminlogin/", views.adminlogin_view, name="admin_login"),
    path("driverlogin/", views.driverlogin_view, name="driver_login"),

    #logout links can be accessed: 
    path("logout-admin/", views.adminlogout_view, name="admin_logout"),
    path("driverlogout/", views.driverlogout_view, name="driver_logout"),
    path("logout/", views.logout_view, name="logout"),

    #other accessible links for every user type:
    path('messages/', views.chat_messages, name='chat_messages'),
    path('send/', views.send_chat_message, name='send_chat_message'),
    path('confirm-email/<str:token>/', views.confirm_email_view, name='confirm-email'),
    path('verify-email/', views.verify_email_view, name='verify-email'),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG == False:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

