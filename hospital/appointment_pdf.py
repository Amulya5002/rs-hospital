
from io import BytesIO
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)


def generate_appointment_pdf(appointment):

    if appointment.status != "Confirmed":
        raise ValueError("Appointment is not confirmed.")

    buffer = BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=40,
        rightMargin=40,
        topMargin=45,
        bottomMargin=40,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "RSTitle",
        parent=styles["Title"],
        fontSize=23,
        textColor=colors.HexColor("#0756a8"),
        alignment=TA_CENTER,
        spaceAfter=12,
    )

    subtitle_style = ParagraphStyle(
        "RSSubtitle",
        parent=styles["Heading2"],
        fontSize=15,
        textColor=colors.HexColor("#123b63"),
        alignment=TA_CENTER,
        spaceAfter=25,
    )

    cell_style = ParagraphStyle(
        "RSCell",
        parent=styles["Normal"],
        fontSize=10,
        leading=15,
        wordWrap="CJK",
    )

    def cell(value):
        return Paragraph(
            escape(str(value if value is not None else "")),
            cell_style
        )

    details = [
        ("Confirmation ID", appointment.confirmation_code),
        ("Patient Name", appointment.patient.full_name),
        ("Email", appointment.patient.email),
        ("Phone", appointment.patient.phone),
        ("Doctor", appointment.doctor.doctor_name),
        ("Department", appointment.doctor.department.department_name),
        (
            "Appointment Date",
            appointment.appointment_date.strftime("%d %B %Y")
        ),
        (
            "Appointment Time",
            appointment.appointment_time.strftime("%I:%M %p")
        ),
        ("Status", appointment.status),
    ]

    data = [
        [cell(label), cell(value)]
        for label, value in details
    ]

    table = Table(
        data,
        colWidths=[150, 360],
        hAlign="CENTER"
    )

    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#eaf4ff")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d6e5f5")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
    ]))

    elements = [
        Paragraph("RS HOSPITAL", title_style),
        Paragraph("APPOINTMENT CONFIRMATION", subtitle_style),
        table,
        Spacer(1, 30),
        Paragraph(
            "Please arrive 15 minutes before your scheduled appointment.",
            styles["Normal"]
        ),
        Spacer(1, 12),
        Paragraph(
            "Thank you for choosing RS Hospital.",
            styles["Normal"]
        ),
    ]

    document.build(elements)

    return buffer.getvalue()
