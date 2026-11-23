from django.http import HttpResponse, HttpResponseForbidden
from .appointment_pdf import generate_appointment_pdf
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from datetime import datetime
from django.db import transaction, IntegrityError
from .models import Patient
from .models import Doctor, Department, Appointment, ContactMessage, Consultation
from .forms import ConsultationForm
from .appointment_email import generate_appointment_pdf
import logging
from django.contrib.auth.models import Group
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
logger = logging.getLogger(__name__)



def home(request):
    return render(request, 'hospital/index.html')


def about(request):
    return render(request, 'hospital/about.html')




def doctor_list(request):
    doctors = Doctor.objects.select_related('department').all()

    return render(request, 'hospital/doctor.html', {
        'doctors': doctors
    })


def speciality(request):
    departments = Department.objects.all()

    return render(
        request,
        'hospital/specaility.html',
        {'departments': departments}
    )


@login_required(login_url='patient_login')
def appointment_page(request):
    
    if (
    request.user.is_staff
    or request.user.is_superuser
    or Doctor.objects.filter(user=request.user).exists()
    or request.user.groups.filter(name='Nurse').exists()
    ):
        return HttpResponseForbidden(
        'Only patients can book appointments.'
    )
    doctors = Doctor.objects.filter(
        is_available=True
    ).select_related('department')

    if request.method == 'POST':

        full_name = request.POST.get('full_name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        date_of_birth = request.POST.get('date_of_birth') or None
        gender = request.POST.get('gender', '')
        doctor_id = request.POST.get('doctor')
        appointment_date = request.POST.get('appointment_date')
        appointment_time = request.POST.get('appointment_time')
        reason = request.POST.get('reason', '').strip()

        try:
            if not all([
                full_name, email, phone, gender,
                doctor_id, appointment_date, appointment_time
            ]):
                raise ValueError(
                    "Please fill in all required fields."
                )

            if gender not in dict(Patient.GENDER_CHOICES):
                raise ValueError("Please select a valid gender.")

            booking_date = datetime.strptime(
                appointment_date, '%Y-%m-%d'
            ).date()

            booking_time = datetime.strptime(
                appointment_time, '%H:%M'
            ).time()

            # Check date and time together.
            booking_datetime = datetime.combine(
                booking_date,
                booking_time
            )

            if timezone.is_naive(booking_datetime):
                booking_datetime = timezone.make_aware(
                    booking_datetime,
                    timezone.get_current_timezone()
                )

            if booking_datetime <= timezone.now():
                raise ValueError(
                    "Please select a future appointment date and time."
                )

            if date_of_birth:
                dob = datetime.strptime(
                    date_of_birth, '%Y-%m-%d'
                ).date()

                if dob > timezone.localdate():
                    raise ValueError(
                        "Date of birth cannot be in the future."
                    )

            else:
                dob = None

            with transaction.atomic():

                # Lock the doctor row while checking the slot.
                doctor = Doctor.objects.select_for_update().get(
                    id=doctor_id,
                    is_available=True
                )

                # Check whether the slot is already booked.
                slot_exists = Appointment.objects.filter(
                    doctor=doctor,
                    appointment_date=booking_date,
                    appointment_time=booking_time
                ).exists()

                if slot_exists:
                    raise ValueError(
                        "This appointment slot is already booked. "
                        "Please select another time."
                    )

                patient, created = Patient.objects.get_or_create(
                    email=email,
                    defaults={
                        'full_name': full_name,
                        'phone': phone,
                        'date_of_birth': dob,
                        'gender': gender,
                    }
                )

                if not created:
                    patient.full_name = full_name
                    patient.phone = phone
                    patient.date_of_birth = dob
                    patient.gender = gender
                    patient.save(
                        update_fields=[
                            'full_name',
                            'phone',
                            'date_of_birth',
                            'gender'
                        ]
                    )

                # Automatically confirm the appointment.
                appointment = Appointment.objects.create(
                    patient=patient,
                    doctor=doctor,
                    appointment_date=booking_date,
                    appointment_time=booking_time,
                    reason=reason,
                    status='Confirmed'
                )

                # Email only after the database commit succeeds.
                

            # Allow this browser session to access its booking PDF.
            request.session['appointment_download_code'] = str(
                appointment.confirmation_code
            )

            messages.success(
                request,
                "Your appointment has been confirmed successfully."
            )

            return redirect(
                'appointment_confirmation',
                confirmation_code=appointment.confirmation_code
            )

        except Doctor.DoesNotExist:
            messages.error(
                request,
                "Please select a valid available doctor."
            )

        except ValueError as error:
            messages.error(request, str(error))

        except IntegrityError:
            messages.error(
                request,
                "The selected slot is no longer available. "
                "Please choose another time."
            )

        except Exception:
            logger.exception("Appointment booking failed")
            messages.error(
                request,
                "Unable to book your appointment. Please try again."
            )

    return render(
        request,
        'hospital/register.html',
        {
            'doctors': doctors,
            'today': timezone.localdate().isoformat()
        }
    )


def appointment_confirmation(request, confirmation_code):

    session_code = request.session.get(
        'appointment_download_code'
    )

    is_staff = (
        request.user.is_authenticated
        and request.user.is_staff
    )

    if not is_staff and session_code != str(confirmation_code):
        return HttpResponseForbidden(
            "You are not authorized to view this appointment."
        )

    appointment = get_object_or_404(
        Appointment.objects.select_related(
            'patient',
            'doctor',
            'doctor__department'
        ),
        confirmation_code=confirmation_code
    )

    return render(
        request,
        'hospital/appointment_confirmation.html',
        {'appointment': appointment}
    )

def contact_page(request):

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        subject = request.POST.get('subject', '').strip()
        message = request.POST.get('message', '').strip()

        if not all([name, email, subject, message]):
            messages.error(request, "Please fill in all fields.")

        else:
            ContactMessage.objects.create(
                name=name,
                email=email,
                subject=subject,
                message=message
            )

            messages.success(
                request,
                "Thank you! Your message has been submitted successfully."
            )

            return redirect('contact_page')

    return render(request, 'hospital/contact.html')


def speciality_detail(request, department_id):

    department = get_object_or_404(
        Department,
        id=department_id
    )

    doctors = Doctor.objects.filter(
        department=department
    )

    speciality_info = {
        'Cardiology': {
            'description': 'Cardiology focuses on the diagnosis, treatment and prevention of heart and blood vessel diseases.',
            'services': [
                'Heart health checkups',
                'ECG and cardiac testing',
                'Blood pressure management',
                'Heart disease treatment',
            ],
        },
        'Neurology': {
            'description': 'Neurology deals with disorders of the brain, spinal cord and nervous system.',
            'services': [
                'Brain and nerve examinations',
                'Headache and migraine treatment',
                'Stroke care',
                'Nerve disorder treatment',
            ],
        },
        'Surgical Gastroenterology': {
            'description': 'Surgical Gastroenterology provides surgical care for conditions affecting the digestive system.',
            'services': [
                'Digestive system surgery',
                'Stomach and intestinal care',
                'Liver and gallbladder surgery',
                'Hernia treatment',
            ],
        },
        'Urology': {
            'description': 'Urology focuses on diseases of the urinary tract and the male reproductive system.',
            'services': [
                'Urinary tract treatment',
                'Kidney stone management',
                'Bladder care',
                'Prostate health',
            ],
        },
        'Pulmonology': {
            'description': 'Pulmonology specializes in diagnosing and treating diseases of the lungs and respiratory system.',
            'services': [
                'Asthma treatment',
                'Lung disease management',
                'Respiratory infection care',
                'Breathing assessments',
            ],
        },
        'Gynecology': {
            'description': 'Gynecology provides healthcare services for women at different stages of life.',
            'services': [
                'Women’s health checkups',
                'Pregnancy-related care',
                'Menstrual health management',
                'Reproductive health consultations',
            ],
        },
        'Orthopaedic & Trauma': {
            'description': 'Orthopaedics focuses on conditions affecting bones, joints, muscles and injuries.',
            'services': [
                'Bone and joint treatment',
                'Fracture management',
                'Sports injury care',
                'Joint pain treatment',
            ],
        },
        'Critical Care': {
            'description': 'Critical Care provides specialized monitoring and treatment for patients with serious medical conditions.',
            'services': [
                'Intensive patient monitoring',
                'Emergency medical support',
                'Critical illness management',
                'Advanced life support',
            ],
        },
    }

    info = speciality_info.get(
        department.department_name,
        {
            'description': 'Our hospital provides specialized medical care for this department.',
            'services': [
                'Specialist consultation',
                'Medical assessment',
                'Treatment and follow-up care',
            ],
        }
    )

    context = {
        'department': department,
        'doctors': doctors,
        'info': info,
    }

    return render(
        request,
        'hospital/speciality_detail.html',
        context
    )


def download_appointment_pdf(request, confirmation_code):

    # Check whether this booking belongs to the current session.
    session_code = request.session.get(
        'appointment_download_code'
    )

    is_staff = (
        request.user.is_authenticated
        and request.user.is_staff
    )

    if not is_staff and session_code != str(confirmation_code):
        return HttpResponseForbidden(
            "You are not authorized to download this appointment PDF."
        )

    appointment = get_object_or_404(
        Appointment.objects.select_related(
            'patient',
            'doctor',
            'doctor__department'
        ),
        confirmation_code=confirmation_code,
        status='Confirmed'
    )

    pdf_content = generate_appointment_pdf(appointment)

    response = HttpResponse(
        pdf_content,
        content_type='application/pdf'
    )

    response['Content-Disposition'] = (
        f'attachment; filename="RS_Appointment_{confirmation_code}.pdf"'
    )

    response['Cache-Control'] = 'no-store'

    return response


def doctor_login(request):

    if request.user.is_authenticated:
        if Doctor.objects.filter(user=request.user).exists():
            return redirect('doctor_dashboard')

    if request.method == 'POST':

        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:

            if Doctor.objects.filter(user=user).exists():
                login(request, user)
                return redirect('doctor_dashboard')

            messages.error(
                request,
                'You do not have doctor access.'
            )

        else:
            messages.error(
                request,
                'Invalid username or password.'
            )

    return render(request, 'hospital/doctor_login.html')


@login_required(login_url='doctor_login')

@login_required(login_url='doctor_login')
def doctor_dashboard(request):

    doctor = Doctor.objects.filter(
        user=request.user
    ).first()

    if doctor is None:
        return HttpResponseForbidden(
            "Doctor access required."
        )

    appointments = Appointment.objects.filter(
        doctor=doctor
    ).select_related(
        'patient'
    ).order_by(
        'appointment_date',
        'appointment_time'
    )

    context = {
        'doctor': doctor,
        'appointments': appointments,

        'total_appointments': appointments.count(),

        'pending_appointments': appointments.filter(
            status='Pending'
        ).count(),

        'confirmed_appointments': appointments.filter(
            status='Confirmed'
        ).count(),

        'completed_appointments': appointments.filter(
            status='Completed'
        ).count(),
    }

    return render(
        request,
        'hospital/doctor_dashboard.html',
        context
    )



@login_required(login_url="staff_login")
@require_POST
def doctor_logout(request):
    logout(request)
    return redirect("home")


@login_required(login_url='doctor_login')
def complete_consultation(request, appointment_id):

    doctor = Doctor.objects.filter(
        user=request.user
    ).first()

    if doctor is None:
        return HttpResponseForbidden(
            "Doctor access required."
        )

    appointment = get_object_or_404(
        Appointment.objects.select_related('patient'),
        id=appointment_id,
        doctor=doctor
    )

    if appointment.status not in ['Confirmed', 'Completed']:
        messages.error(
            request,
            "This appointment is not ready for completion."
        )
        return redirect('doctor_dashboard')

    if hasattr(appointment, 'consultation'):
        messages.info(
            request,
            "This consultation has already been completed."
        )
        return redirect('doctor_dashboard')

    if request.method == 'POST':

        form = ConsultationForm(request.POST)

        if form.is_valid():

            with transaction.atomic():

                locked_appointment = (
                    Appointment.objects.select_for_update()
                    .get(pk=appointment.pk, doctor=doctor)
                )

                if (
                    locked_appointment.status != 'Confirmed'
                    or Consultation.objects.filter(
                        appointment=locked_appointment
                    ).exists()
                ):
                    messages.error(
                        request,
                        "Consultation is already completed "
                        "or cannot be completed."
                    )
                    return redirect('doctor_dashboard')

                consultation = form.save(commit=False)
                consultation.appointment = locked_appointment
                consultation.save()

                locked_appointment.status = 'Completed'
                locked_appointment.save(
                    update_fields=['status']
                )

            messages.success(
                request,
                "Consultation completed successfully."
            )

            return redirect('doctor_dashboard')

    else:
        form = ConsultationForm()

    return render(
        request,
        'hospital/complete_consultation.html',
        {
            'appointment': appointment,
            'form': form,
        }
    )


def nurse_login(request):

    if request.user.is_authenticated:
        if request.user.groups.filter(name='Nurse').exists():
            return redirect('nurse_dashboard')

    if request.method == 'POST':

        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None and user.groups.filter(
            name='Nurse'
        ).exists():

            login(request, user)
            return redirect('nurse_dashboard')

        messages.error(
            request,
            'Invalid credentials or nurse access denied.'
        )

    return render(request, 'hospital/nurse_login.html')


@login_required(login_url='nurse_login')
def nurse_dashboard(request):

    if not request.user.groups.filter(name='Nurse').exists():
        return HttpResponseForbidden(
            'Nurse access required.'
        )

    consultations = Consultation.objects.select_related(
        'appointment__patient',
        'appointment__doctor',
        'dispensed_by'
    ).order_by('-completed_at')

    return render(
        request,
        'hospital/nurse_dashboard.html',
        {'consultations': consultations}
    )


@require_POST
@login_required(login_url='nurse_login')
def mark_dispensed(request, consultation_id):

    if not request.user.groups.filter(name='Nurse').exists():
        return HttpResponseForbidden(
            'Nurse access required.'
        )

    with transaction.atomic():

        consultation = get_object_or_404(
            Consultation.objects.select_for_update(),
            id=consultation_id
        )

        if consultation.dispensing_status == 'Dispensed':
            messages.info(
                request,
                'Medicine handover already recorded.'
            )
            return redirect('nurse_dashboard')

        consultation.dispensing_status = 'Dispensed'
        consultation.dispensed_by = request.user
        consultation.dispensed_at = timezone.now()

        consultation.save(
            update_fields=[
                'dispensing_status',
                'dispensed_by',
                'dispensed_at'
            ]
        )

    messages.success(
        request,
        'Medicine handover recorded successfully.'
    )

    return redirect('nurse_dashboard')



def staff_login(request):

    if request.user.is_authenticated:

        if Doctor.objects.filter(user=request.user).exists():
            return redirect('doctor_dashboard')

        if request.user.groups.filter(name='Nurse').exists():
            return redirect('nurse_dashboard')

    if request.method == 'POST':

        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:

            if Doctor.objects.filter(user=user).exists():
                login(request, user)
                return redirect('doctor_dashboard')

            elif user.groups.filter(name='Nurse').exists():
                login(request, user)
                return redirect('nurse_dashboard')

            else:
                messages.error(
                    request,
                    'Only doctors and nurses can access staff login.'
                )

        else:
            messages.error(
                request,
                'Invalid username or password.'
            )

    return render(request, 'hospital/staff_login.html')



def patient_login(request):

    # Already logged-in patients go to Home.
    if request.user.is_authenticated:

        is_staff_user = (
            request.user.is_staff
            or request.user.is_superuser
            or Doctor.objects.filter(user=request.user).exists()
            or request.user.groups.filter(name='Nurse').exists()
        )

        if not is_staff_user:
            return redirect('home')

    if request.method == 'POST':

        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is None:
            messages.error(
                request,
                'Invalid username or password.'
            )

        elif (
            user.is_staff
            or user.is_superuser
            or Doctor.objects.filter(user=user).exists()
            or user.groups.filter(name='Nurse').exists()
        ):
            messages.error(
                request,
                'Please use Staff Login.'
            )

        else:
            login(request, user)

            messages.success(
                request,
                f'Welcome, {user.get_full_name() or user.username}!'
            )

            # Always go to the website homepage.
            return redirect('home')

    return render(
        request,
        'hospital/patient_login.html'
    )

@login_required(login_url='patient_login')
def patient_dashboard(request):

    patient = Patient.objects.filter(
        user=request.user
    ).first()

    if patient is None:
        return HttpResponseForbidden(
            'Patient access required.'
        )

    appointments = Appointment.objects.filter(
        patient=patient
    ).select_related('doctor').order_by(
        '-appointment_date',
        '-appointment_time'
    )

    return render(
        request,
        'hospital/patient_dashboard.html',
        {
            'patient': patient,
            'appointments': appointments
        }
    )



def patient_signup(request):

    User = get_user_model()

    if request.method == 'POST':

        full_name = request.POST.get(
            'full_name', ''
        ).strip()

        username = request.POST.get(
            'username', ''
        ).strip()

        password = request.POST.get(
            'password', ''
        )

        if not full_name or not username or not password:
            messages.error(
                request,
                'All fields are required.'
            )
            return render(
                request,
                'hospital/patient_signup.html'
            )

        if len(full_name) > 100:
            messages.error(
                request,
                'Full name is too long.'
            )
            return redirect('patient_signup')

        if User.objects.filter(
            username__iexact=username
        ).exists():

            messages.error(
                request,
                'Username already exists.'
            )
            return redirect('patient_signup')

        try:
            candidate = User(username=username)
            candidate.full_name = full_name

            validate_password(password, user=candidate)

            # Validates username using the configured user model.
            candidate.full_clean(
                exclude=['password'],
                validate_unique=True
            )

        except ValidationError as error:
            for message in error.messages:
                messages.error(request, message)

            return redirect('patient_signup')

        # Split full name for Django's default User fields.
        name_parts = full_name.split(' ', 1)

        first_name = name_parts[0]
        last_name = (
            name_parts[1]
            if len(name_parts) > 1
            else ''
        )

        user = User.objects.create_user(
            username=username,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )

        messages.success(
            request,
            'Signup successful! Please sign in.'
        )

        return redirect('patient_login')

    return render(
        request,
        'hospital/patient_signup.html'
    )


from django.contrib.auth import logout
from django.views.decorators.http import require_POST


@require_POST
def patient_logout(request):

    logout(request)

    messages.success(
        request,
        'You have logged out successfully.'
    )

    return redirect('home')
