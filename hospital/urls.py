from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
   path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('doctors/', views.doctor_list, name='doctor_list'),
    path('specialities/', views.speciality, name='speciality'),
    path('appointment/', views.appointment_page, name='appointment_page'),
    path('contact/', views.contact_page, name='contact_page'),


    path('appointment/confirmation/<uuid:confirmation_code>/', views.appointment_confirmation, name='appointment_confirmation'),
    path(
    'specialities/<int:department_id>/',
    views.speciality_detail,
    name='speciality_detail'
   ),
   path(
    'appointment/download/<uuid:confirmation_code>/',
    views.download_appointment_pdf,
    name='download_appointment_pdf'
   ),
   path(
    'specialities/<int:department_id>/',
    views.speciality_detail,
    name='speciality_detail'
),
path(
    'doctor/login/',
    views.doctor_login,
    name='doctor_login'
),

path(
    'doctor/dashboard/',
    views.doctor_dashboard,
    name='doctor_dashboard'
),

path(
    'doctor/logout/',
    views.doctor_logout,
    name='doctor_logout'
),

path(
    'doctor/consultation/<int:appointment_id>/',
    views.complete_consultation,
    name='complete_consultation'
),

path(
    'nurse/login/',
    views.nurse_login,
    name='nurse_login'
),

path(
    'nurse/dashboard/',
    views.nurse_dashboard,
    name='nurse_dashboard'
),

path(
    'nurse/dispensed/<int:consultation_id>/',
    views.mark_dispensed,
    name='mark_dispensed'
),

# Common Staff Login
path(
    'staff/login/',
    views.staff_login,
    name='staff_login'
),
path("staff/logout/", views.doctor_logout, name="doctor_logout"),

# Patient Login
path(
    'patient/login/',
    views.patient_login,
    name='patient_login'
),

# Patient Dashboard
path(
    'patient/dashboard/',
    views.patient_dashboard,
    name='patient_dashboard'
),
path(
    'patient/signup/',
    views.patient_signup,
    name='patient_signup'
),
path(
    'patient/logout/',
    views.patient_logout,
    name='patient_logout'
),
]

