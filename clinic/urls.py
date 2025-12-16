from django.urls import path
from . import views
from django.contrib.auth import views as auth_views


urlpatterns = [
    path('', views.home, name='home'),
    path('drugs/', views.drug_list, name='drug_list'),
    path('drugs/<int:pk>/', views.drug_detail, name='drug_detail'),
    path('book/', views.book_injection, name='book_injection'),
    path('cart/add/<int:drug_id>/', views.cart_add, name='cart_add'),
    path('cart/', views.cart_detail, name='cart_detail'),
    path('cart/remove/<int:drug_id>/', views.cart_remove, name='cart_remove'),
    path('checkout/', views.checkout, name='checkout'),
    path('verify-payment/', views.verify_payment, name='verify_payment'),
    path('save-customer-info/', views.save_customer_info, name='save_customer_info'),
    path('register/', views.register, name='register'),
    # clinic/urls.py
    path('order-history/', views.order_history, name='order_history'),

    # Custom Password Reset URLs
    # path('password-reset/', views.custom_password_reset, name='custom_password_reset'),
    # path('password-reset-confirm/<uidb64>/<token>/', views.custom_password_reset_confirm, name='custom_password_reset_confirm'),
    
#     path('password-reset/',
#      auth_views.PasswordResetView.as_view(template_name='clinic/password_reset.html'),
#      name='password_reset'),
# path('password-reset/done/',
#      auth_views.PasswordResetDoneView.as_view(template_name='clinic/password_reset_done.html'),
#      name='password_reset_done'),
#    path('password-reset-confirm/<uidb64>/<token>/',
#          auth_views.PasswordResetConfirmView.as_view(
#              template_name='clinic/password_reset_confirm.html',
#              success_url='/login/'  # or '/password-reset/done/'
#          ),
#          name='password_reset_confirm'),



    path('password-reset/', views.request_password_reset, name='password_reset'),
    path('password-reset-confirm/<uidb64>/<token>/', views.password_reset_confirm, name='password_reset_confirm')
    # AUTH URLs - Essential for login/logout
    # path('accounts/login/', 
    #      auth_views.LoginView.as_view(template_name='registration/login.html'), 
    #      name='login'),
    
    # path('accounts/logout/', 
    #      auth_views.LogoutView.as_view(), 
    #      name='logout'),
     # ... your other URLs
    
]