
import logging

from django.conf import settings
from django.core.mail import EmailMessage

from .models import Appointment
from .appointment_pdf import generate_appointment_pdf

logger = logging.getLogger(__name__)


def send_appointment_confirmation_email(appointment_id):

    appointment = Appointment.objects.select_related(
        "patient",
        "doctor",
        "doctor__department"
    ).get(pk=appointment_id)

    if appointment.status != "Confirmed":
        return

    pdf_content = generate_appointment_pdf(appointment)

    subject = "RS Hospital - Confirmed Appointment"

    message = f"""
Dear {appointment.patient.full_name},

Your appointment has been confirmed successfully.

Confirmation ID: {appointment.confirmation_code}
Doctor: {appointment.doctor.doctor_name}
Department: {appointment.doctor.department.department_name}
Date: {appointment.appointment_date.strftime('%d %B %Y')}
Time: {appointment.appointment_time.strftime('%I:%M %p')}
Status: Confirmed

Your appointment confirmation PDF is attached.

Please arrive 15 minutes before your scheduled time.

Thank you for choosing RS Hospital.

Regards,
RS Hospital Team
"""

    email = EmailMessage(
        subject=subject,
        body=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[appointment.patient.email],
    )

    email.attach(
        filename=f"RS_Appointment_{appointment.confirmation_code}.pdf",
        content=pdf_content,
        mimetype="application/pdf",
    )

    email.send(fail_silently=False)


def send_appointment_email_safely(appointment_id):
    try:
        send_appointment_confirmation_email(appointment_id)
    except Exception:
        logger.exception(
            "Failed to email appointment %s",
            appointment_id
        )
