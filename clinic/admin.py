from django.contrib import admin
from .models import Drug, DrugCategory, InjectionCategory, Booking, Order, OrderItem

# Register all models once
admin.site.register(DrugCategory)
admin.site.register(Drug)
admin.site.register(InjectionCategory)
admin.site.register(Booking)
admin.site.register(Order)        # ← Only once!
admin.site.register(OrderItem)    # ← Only once!