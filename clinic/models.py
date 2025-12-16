# clinic/models.py
import os
from django.db import models
from django.core.exceptions import ValidationError
from datetime import time, date

def drug_image_path(instance, filename):
    ext = filename.split('.')[-1]
    name = instance.name.replace(' ', '_').lower()
    return f'drugs/{name}.{ext}'

class DrugCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class Drug(models.Model):
    name = models.CharField(max_length=200)
    category = models.ForeignKey(DrugCategory, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Price in NGN (₦)")
    stock = models.PositiveIntegerField()
    image = models.ImageField(upload_to=drug_image_path, blank=True, null=True)

    def __str__(self):
        return self.name

    @property
    def formatted_price(self):
        return f"₦{self.price:,.2f}"

class InjectionCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class Booking(models.Model):
    injection_category = models.ForeignKey(InjectionCategory, on_delete=models.CASCADE)
    patient_name = models.CharField(max_length=200)
    phone = models.CharField(max_length=15)  # 👈 Added phone
    date = models.DateField()
    start_time = models.TimeField()

    class Meta:
        unique_together = ('injection_category', 'date', 'start_time')

    
# clinic/models.py
    def clean(self):
               if self.start_time is None:
                 return  # Skip if not set
               from datetime import time, date
               if not (time(8, 0) <= self.start_time <= time(20, 0)):
                   raise ValidationError("Booking time must be between 08:00 and 20:00.")
               if self.date and self.date < date.today():
                   raise ValidationError("Cannot book for past dates.")
    
    def __str__(self):
        return f"{self.patient_name} - {self.injection_category} on {self.date} at {self.start_time}"
# models.py
# Add these at the bottom of your models.py
# clinic/models.py
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator

class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    reference = models.CharField(max_length=100, unique=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Customer info (snapshot at time of order)
    name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(
        max_length=15,
        validators=[RegexValidator(r'^\+?1?\d{9,15}$')]
    )
    address = models.TextField()
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order {self.reference} by {self.user.username}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    drug = models.ForeignKey(Drug, on_delete=models.CASCADE)  # assuming you have Drug model
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)  # price at time of purchase

    def __str__(self):
        return f"{self.quantity}x {self.drug.name}"