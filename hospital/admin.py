from .models import ContactMessage
from .models import Doctor
from django.contrib import admin
from .models import (
    Department,
    Doctor,
    Patient,
    Appointment,
    ContactMessage
)

admin.site.register(Department)

admin.site.register(Patient)
admin.site.register(Appointment)

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'subject', 'created_at')
    search_fields = ('name', 'email', 'subject')
    list_filter = ('created_at',)

@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = (
        'doctor_name',
        'qualification',
        'department',
        'experience_years',
        'is_available',
    )

    list_filter = ('department', 'is_available')

    search_fields = ('doctor_name', 'qualification', 'email')