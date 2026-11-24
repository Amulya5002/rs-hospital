
from django.contrib import admin

from .models import (
    Department,
    Doctor,
    Patient,
    Appointment,
    ContactMessage,
    Consultation
)


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'department_name')
    search_fields = ('department_name',)


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'doctor_name',
        'qualification',
        'department',
        'experience_years',
        'is_available',
        'user',
    )

    list_filter = (
        'department',
        'is_available',
    )

    search_fields = (
        'doctor_name',
        'qualification',
        'email',
        'user__username',
    )

    autocomplete_fields = ('user',)


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):

    list_display = (
        'full_name',
        'email',
        'phone',
        'gender',
        'user',
    )

    search_fields = (
        'full_name',
        'email',
        'phone',
    )


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):

    list_display = (
        'patient',
        'doctor',
        'appointment_date',
        'appointment_time',
        'status',
    )

    list_filter = (
        'status',
        'appointment_date',
        'doctor',
    )

    search_fields = (
        'patient__full_name',
        'doctor__doctor_name',
    )


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):

    list_display = (
        'name',
        'email',
        'subject',
        'created_at',
    )

    search_fields = (
        'name',
        'email',
        'subject',
    )

    list_filter = ('created_at',)


@admin.register(Consultation)
class ConsultationAdmin(admin.ModelAdmin):

    list_display = (
        'appointment',
        'completed_at',
        'dispensing_status',
        'dispensed_by',
        'dispensed_at',
    )

    list_filter = (
        'dispensing_status',
        'completed_at',
    )

    search_fields = (
        'appointment__patient__full_name',
        'appointment__doctor__doctor_name',
    )

    readonly_fields = (
        'completed_at',
        'dispensed_by',
        'dispensed_at',
        'dispensing_status',
    )
