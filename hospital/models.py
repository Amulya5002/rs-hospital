import uuid
from django.db import models
from django.conf import settings

# 1. Department Table
class Department(models.Model):
    department_name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.department_name


# 2. Doctor Table
class Doctor(models.Model):
    
    doctor_name = models.CharField(max_length=100)
    qualification = models.CharField(max_length=100)
    experience_years = models.PositiveIntegerField(default=0)

    department = models.ForeignKey(
        Department,
        on_delete=models.PROTECT,
        related_name='doctors'
    )

    image = models.ImageField(
    upload_to='doctors/',
    null=True,
    blank=True
)

    phone = models.CharField(max_length=15, blank=True)
    email = models.EmailField(blank=True)
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return self.doctor_name

    user = models.OneToOneField(
    settings.AUTH_USER_MODEL,
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
    related_name='doctor_profile'
)


# 3. Patient Table
class Patient(models.Model):

    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other'),
    ]

    user = models.OneToOneField(
    settings.AUTH_USER_MODEL,
    on_delete=models.CASCADE,
    null=True,
    blank=True
)

    full_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15)
    date_of_birth = models.DateField(null=True, blank=True)
    
    gender = models.CharField(
        max_length=10,
        choices=GENDER_CHOICES
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.full_name

    



# 4. Appointment Table
class Appointment(models.Model):

    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Confirmed', 'Confirmed'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
    ]

    confirmation_code = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False
        
    )

    patient = models.ForeignKey(
        Patient,
        on_delete=models.PROTECT
    )

    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.PROTECT
    )

    appointment_date = models.DateField()
    appointment_time = models.TimeField()
    reason = models.TextField(blank=True)

    status = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default='Pending'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    'doctor',
                    'appointment_date',
                    'appointment_time'
                ],
                name='unique_doctor_appointment_slot'
            )
        ]

    def __str__(self):
        return f"{self.patient} - {self.doctor}"


# 5. Contact Message Table
class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.subject




class Consultation(models.Model):

    DISPENSING_CHOICES = [
        ('Pending', 'Pending'),
        ('Dispensed', 'Dispensed'),
    ]

    appointment = models.OneToOneField(
        Appointment,
        on_delete=models.PROTECT,
        related_name='consultation'
    )

    diagnosis = models.TextField()

    prescription = models.TextField(
        help_text="Medicine, strength, dose, route, frequency and duration"
    )

    doctor_notes = models.TextField(blank=True)

    advice = models.TextField(blank=True)

    completed_at = models.DateTimeField(
        auto_now_add=True
    )

    dispensing_status = models.CharField(
        max_length=15,
        choices=DISPENSING_CHOICES,
        default='Pending'
    )

    dispensed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='dispensed_consultations'
    )

    dispensed_at = models.DateTimeField(
        null=True,
        blank=True
    )

    def __str__(self):
        return (
            f"{self.appointment.patient.full_name} - "
            f"{self.appointment.doctor.doctor_name}"
        )
