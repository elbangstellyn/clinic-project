from django import forms
from .models import Booking, InjectionCategory
from datetime import time, date

# clinic/forms.py


# Fixed time slots as strings (for form)
SLOT_CHOICES = [
    ("08:00", "8:00 AM – 9:00 AM"),
    ("09:00", "9:00 AM – 10:00 AM"),
    ("10:00", "10:00 AM – 11:00 AM"),
    ("11:00", "11:00 AM – 12:00 PM"),
    ("12:00", "12:00 PM – 1:00 PM"),
    ("13:00", "1:00 PM – 2:00 PM"),
    ("14:00", "2:00 PM – 3:00 PM"),
    ("15:00", "3:00 PM – 4:00 PM"),
    ("16:00", "4:00 PM – 5:00 PM"),
    ("17:00", "5:00 PM – 6:00 PM"),
    ("18:00", "6:00 PM – 7:00 PM"),
    ("19:00", "7:00 PM – 8:00 PM"),
    ("20:00", "8:00 PM – 9:00 PM"),
]

class BookingForm(forms.ModelForm):
    start_time = forms.ChoiceField(choices=SLOT_CHOICES)

    class Meta:
        model = Booking
        fields = ['injection_category', 'patient_name', 'phone', 'date', 'start_time']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'min': date.today().isoformat()}),
            'phone': forms.TextInput(attrs={'placeholder': 'e.g. 09039871169'}),
        }

    def clean_start_time(self):
        # Convert "09:00" → time(9, 0)
        time_str = self.cleaned_data['start_time']
        hour = int(time_str.split(':')[0])
        return time(hour, 0)

class CustomerInfoForm(forms.Form):
    name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'placeholder': 'Full Name'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'placeholder': 'Email'}))
    phone = forms.CharField(max_length=15, widget=forms.TextInput(attrs={'placeholder': 'Phone Number'}))
    address = forms.CharField(widget=forms.Textarea(attrs={'placeholder': 'Delivery Address', 'rows': 3}))