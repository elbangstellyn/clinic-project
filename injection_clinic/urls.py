from django.contrib import admin
from django.urls import path, include
from clinic import views
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView 

urlpatterns = [
    path('blessing/admin', admin.site.urls),
    path('', views.home, name='home'),
    # path('accounts/', include('django.contrib.auth.urls')),  # Keep this for login/logout
    path('', include('clinic.urls')),
     # Add built-in auth URLs (optional but convenient)
    path('accounts/login/', auth_views.LoginView.as_view(), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('password-reset/', views.request_password_reset, name='password_reset'),
    
    # ✅ Add this line:
    path('password-reset/done/',
         TemplateView.as_view(template_name='clinic/password_reset_done.html'),
         name='password_reset_done'),
    
    path('password-reset-confirm/<uidb64>/<token>/', 
         views.password_reset_confirm, 
         name='password_reset_confirm'),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)







