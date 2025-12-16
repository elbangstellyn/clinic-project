import requests
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.conf import settings
from .models import Drug, DrugCategory, InjectionCategory, Booking, Order, OrderItem
from .forms import BookingForm, CustomerInfoForm 
from .cart import Cart

# ======================
# DRUG & CART VIEWS
# ======================

def drug_list(request):
    drugs = Drug.objects.select_related('category').all()
    return render(request, 'clinic/drugs/list.html', {'drugs': drugs})

def drug_detail(request, pk):
    drug = get_object_or_404(Drug, pk=pk)
    return render(request, 'clinic/drugs/detail.html', {'drug': drug})

def cart_add(request, drug_id):
    cart = Cart(request)
    drug = get_object_or_404(Drug, id=drug_id)

    # Get current quantity in cart
    current_qty = cart.cart.get(str(drug_id), {}).get('quantity', 0)

    if current_qty >= drug.stock:
        messages.error(
            request,
            f"Cannot add more '{drug.name}'. Max {drug.stock} allowed."
        )
    else:
        cart.add(drug_id=drug_id, quantity=1)
        messages.success(request, f"{drug.name} added to cart.")

    # ✅ Redirect back to drug list (or detail if you prefer)
    return redirect('drug_list')  # ← was 'cart_detail'

def cart_detail(request):
    cart = Cart(request)
    
    # Optional: Clean cart on view
    removed_items = []
    for item in list(cart):  # list() to avoid dict size change during iteration
        drug = item['drug']
        if drug.stock < item['quantity']:
            removed_items.append(drug.name)
            cart.cart.pop(str(drug.id), None)
            cart.save()
    
    if removed_items:
        messages.warning(
            request,
            f"Some items were removed from your cart due to low stock: {', '.join(removed_items)}"
        )

    return render(request, 'clinic/cart/detail.html', {'cart': cart})

def cart_remove(request, drug_id):
    cart = Cart(request)
    cart.cart.pop(str(drug_id), None)
    cart.save()
    return redirect('cart_detail')

 # ← add CustomerInfoForm
from django.contrib.auth.decorators import login_required

@login_required  # ← Add this
def checkout(request):
    cart = Cart(request)
    if not cart:
        messages.error(request, "Your cart is empty.")
        return redirect('drug_list')
    
    # 🔍 Validate stock for all items in cart
    out_of_stock_items = []
    total = 0

    for item in cart:
        drug = item['drug']
        requested_qty = item['quantity']
        if drug.stock < requested_qty:
            out_of_stock_items.append(drug.name)
            # Remove from cart
            cart.cart.pop(str(drug.id), None)
            cart.save()

    if out_of_stock_items:
        messages.error(
            request,
            f"The following items are no longer available: {', '.join(out_of_stock_items)}. "
            "They have been removed from your cart."
        )
        return redirect('cart_detail')

    # If all items are in stock, proceed
    total = cart.get_total_price()
    amount_kobo = int(total * 100)

    if request.method == 'POST':
        form = CustomerInfoForm(request.POST)
        if form.is_valid():
            request.session['customer_info'] = form.cleaned_data
            messages.success(request, "Customer info saved!")
            return redirect('checkout')
    else:
        initial = request.session.get('customer_info', {})
        form = CustomerInfoForm(initial=initial)

    context = {
        'cart': cart,
        'total': total,
        'amount_kobo': amount_kobo,
        'paystack_public_key': getattr(settings, 'PAYSTACK_PUBLIC_KEY', 'pk_test_xxx'),
        'form': form,
    }
    return render(request, 'clinic/cart/checkout.html', context)



def verify_payment(request):
    ref = request.GET.get('reference')
    if not ref:
        messages.error(request, "No payment reference found.")
        return redirect('checkout')

    # 🔒 Verify with Paystack API (use test key for now)
    url = f"https://api.paystack.co/transaction/verify/{ref}"
    headers = {
        "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response_data = response.json()

        # For testing: skip real verification and assume success
        # Remove this block when using real Paystack keys
        if settings.DEBUG:
            success = True
        else:
            success = response_data.get('status') and response_data['data']['status'] == 'success'

        if success:
            cart = Cart(request)
            customer = request.session.get('customer_info', {})
            
            if not cart or not customer:
                messages.error(request, "Missing cart or customer info.")
                return redirect('checkout')

            # ✅ Now 'Order' is defined!
            order = Order.objects.create(
                name=customer['name'],
                email=customer['email'],
                phone=customer['phone'],
                address=customer['address'],
                total=cart.get_total_price(),
                reference=ref
            )

            # Save order items & deduct stock
            for item in cart:
                drug = item['drug']
                quantity = item['quantity']
                drug.stock -= quantity
                drug.save()
                OrderItem.objects.create(
                    order=order,
                    drug=drug,
                    quantity=quantity,
                    price=item['price']
                )

            cart.clear()
            messages.success(request, f"Payment successful! Order #{order.id} confirmed.")
            return redirect('drug_list')
        else:
            messages.error(request, "Payment verification failed.")
            return redirect('checkout')

    except requests.exceptions.RequestException as e:
        messages.error(request, "Error verifying payment. Please try again.")
        return redirect('checkout')
# ======================
# INJECTION BOOKING VIEW
# ======================

# clinic/views.py
from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import BookingForm
from .models import Booking
from datetime import date

def book_injection(request):
    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, "✅ Booking confirmed!")
                return redirect('book_injection')
            except Exception as e:
                # This catches IntegrityError from unique_together
                messages.error(request, "❌ This time slot is already booked. Please choose another.")
        else:
            messages.error(request, "Please fix the errors below.")
    else:
        form = BookingForm(initial={'date': date.today()})

    return render(request, 'clinic/bookings/book.html', {'form': form})

def home(request):
    # You can add dynamic content here later (e.g., from a model)
    healthy_tips = [
        "Drink at least 8 glasses of water daily.",
        "Eat a balanced diet rich in fruits and vegetables.",
        "Exercise for at least 30 minutes most days of the week.",
        "Get 7–9 hours of sleep every night.",
        "Avoid self-medication — consult a pharmacist or doctor.",
        "Wash hands frequently to prevent infections.",
        "Schedule regular health check-ups.",
    ]
    return render(request, 'clinic/home.html', {'healthy_tips': healthy_tips})


from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect
from .forms import CustomerInfoForm

@csrf_protect
def save_customer_info(request):
    if request.method == 'POST':
        form = CustomerInfoForm(request.POST)
        if form.is_valid():
            # Save to session
            request.session['customer_info'] = form.cleaned_data
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'errors': form.errors})
    return JsonResponse({'success': False})


from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django import forms
from django.contrib.auth.models import User
from django.contrib import messages

class CustomUserCreationForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ("first_name", "last_name", "email", "password1", "password2")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data["email"]  # Use email as username
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        if commit:
            user.save()
        return user

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Account created successfully!")
            return redirect('home')
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/register.html', {'form': form})



# from django.shortcuts import render, redirect
# from django.contrib.auth.models import User
# from django.contrib.auth.tokens import default_token_generator
# from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
# from django.utils.encoding import force_bytes, force_str
# from django.core.mail import send_mail
# from django.conf import settings
# from django.contrib import messages
# from django.http import HttpResponse

# def custom_password_reset(request):
#     if request.method == 'POST':
#         email = request.POST.get('email')
#         try:
#             user = User.objects.get(email=email)
            
#             # Generate token and uid
#             token = default_token_generator.make_token(user)
#             uid = urlsafe_base64_encode(force_bytes(user.pk))
            
#             # Create reset link
#             reset_url = f"{request.scheme}://{request.get_host()}/password-reset-confirm/{uid}/{token}/"
            
#             # Send email
#             send_mail(
#                 'Password Reset Request - Clinic',
#                 f'Click this link to reset your password: {reset_url}',
#                 settings.DEFAULT_FROM_EMAIL,
#                 [email],
#                 fail_silently=False,
#             )
            
#             messages.success(request, 'Password reset link has been sent to your email.')
#             return redirect('custom_password_reset')
            
#         except User.DoesNotExist:
#             messages.error(request, 'No user found with this email address.')
    
#     return render(request, 'clinic/custom_password_reset.html')  # Make sure this matches your template name

# def custom_password_reset_confirm(request, uidb64, token):
#     try:
#         uid = force_str(urlsafe_base64_decode(uidb64))
#         user = User.objects.get(pk=uid)
        
#         if default_token_generator.check_token(user, token):
#             if request.method == 'POST':
#                 new_password = request.POST.get('new_password')
#                 confirm_password = request.POST.get('confirm_password')
                
#                 if new_password == confirm_password:
#                     user.set_password(new_password)
#                     user.save()
#                     messages.success(request, 'Password has been reset successfully. You can now login with your new password.')
#                     return redirect('login')
#                 else:
#                     messages.error(request, 'Passwords do not match.')
            
#             return render(request, 'clinic/custom_password_reset_confirm.html')  # Make sure this matches your template name
#         else:
#             return HttpResponse('Invalid or expired reset link.')
            
#     except (TypeError, ValueError, OverflowError, User.DoesNotExist):
#         return HttpResponse('Invalid reset link.')


# clinic/views.py
# clinic/views.py
import requests
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.conf import settings
from .models import Order, OrderItem
from .cart import Cart  # assuming you have a Cart class


@login_required
def verify_payment(request):
    ref = request.GET.get('reference')
    if not ref:
        messages.error(request, "No payment reference found.")
        return redirect('checkout')

    # 🔒 Verify with Paystack API — FIX: no spaces in URL!
    url = f"https://api.paystack.co/transaction/verify/{ref}"  # ✅ Fixed URL
    headers = {
        "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response_data = response.json()

        # In production, always verify from Paystack
        if settings.DEBUG:
            # Only for local testing — simulate success
            success = True
            amount_paid = 10000  # dummy amount in kobo
            email = request.user.email
        else:
            success = (
                response_data.get('status') is True and
                response_data['data']['status'] == 'success'
            )
            amount_paid = response_data['data']['amount']  # in kobo
            email = response_data['data']['customer']['email']

        if success:
            cart = Cart(request)
            customer = request.session.get('customer_info', {})

            if not cart.cart:  # assuming cart.cart is the dict of items
                messages.warning(request, "Your cart is empty.")
                return redirect('drug_list')

            if not customer:
                messages.error(request, "Customer information is missing.")
                return redirect('checkout')

            # Optional: validate email matches (for security)
            if not settings.DEBUG and customer.get('email') != email:
                messages.error(request, "Payment email does not match order.")
                return redirect('checkout')

            # Create order
            order = Order.objects.create(
                user=request.user,  # ✅ associate with logged-in user
                name=customer['name'],
                email=customer['email'],
                phone=customer['phone'],
                address=customer['address'],
                total_amount=cart.get_total_price(),  # ✅ use total_amount if that's your field
                reference=ref,
                status='paid'
            )

            # Save order items & deduct stock
            for item in cart:
                drug = item['drug']
                quantity = item['quantity']
                # Ensure enough stock (double-check)
                if drug.stock < quantity:
                    messages.error(request, f"Not enough stock for {drug.name}.")
                    # Optionally: delete order or mark as failed
                    order.delete()
                    return redirect('cart_detail')

                drug.stock -= quantity
                drug.save()

                OrderItem.objects.create(
                    order=order,
                    drug=drug,
                    quantity=quantity,
                    price=item['price']
                )

            # Clear cart and customer info
            cart.clear()
            if 'customer_info' in request.session:
                del request.session['customer_info']

            messages.success(request, f"Payment successful! Order #{order.id} confirmed.")
            return redirect('order_history')  # ✅ redirect to order history

        else:
            messages.error(request, "Payment verification failed. Please contact support.")
            return redirect('checkout')

    except requests.exceptions.Timeout:
        messages.error(request, "Payment verification timed out. Please wait and check your email.")
        return redirect('checkout')
    except requests.exceptions.RequestException as e:
        messages.error(request, "Error connecting to payment gateway. Please try again.")
        return redirect('checkout')
    except Exception as e:
        # Log error in production
        messages.error(request, "An unexpected error occurred.")
        return redirect('checkout')


# clinic/views.py
@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'clinic/order_history.html', {'orders': orders})


# clinic/views.py
# from django.shortcuts import render, redirect
# from django.contrib import messages
# from django.contrib.auth import get_user_model
# from django.contrib.auth.tokens import default_token_generator
# from django.utils.http import urlsafe_base64_encode
# from django.utils.encoding import force_bytes
# from django.core.mail import send_mail
# from django.conf import settings

# User = get_user_model()




# clinic/views.py
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.password_validation import validate_password

User = get_user_model()

def request_password_reset(request):
    if request.method == "POST":
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            messages.success(request, "If your email is registered, you'll receive a reset link.")
            return redirect('password_reset_done')
        
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        reset_url = request.build_absolute_uri(f"/password-reset-confirm/{uid}/{token}/")
        
        send_mail(
            subject="Password Reset Request",
            message=f"Click to reset: {reset_url}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
        )
        messages.success(request, "If your email is registered, you'll receive a reset link.")
        return redirect('password_reset_done')
    
    return render(request, 'clinic/password_reset.html')


def password_reset_confirm(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        if request.method == "POST":
            password1 = request.POST.get("password1")
            password2 = request.POST.get("password2")
            if password1 != password2:
                messages.error(request, "Passwords do not match.")
            else:
                try:
                    validate_password(password1, user)
                    user.set_password(password1)
                    user.save()
                    login(request, user)
                    messages.success(request, "Your password has been reset.")
                    return redirect('home')
                except Exception as e:
                    messages.error(request, str(e))
        return render(request, 'clinic/password_reset_confirm.html')
    else:
        messages.error(request, "The reset link is invalid or has expired.")
        return redirect('password_reset')