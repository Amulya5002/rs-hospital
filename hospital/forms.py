
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from .models import Patient,Consultation

User = get_user_model()


class PatientRegistrationForm(forms.Form):

    username = forms.CharField(max_length=150)

    full_name = forms.CharField(max_length=100)

    email = forms.EmailField()

    phone = forms.CharField(max_length=15)

    date_of_birth = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'})
    )

    gender = forms.ChoiceField(
        choices=[
            ('Male', 'Male'),
            ('Female', 'Female'),
            ('Other', 'Other'),
        ]
    )

    password = forms.CharField(
        widget=forms.PasswordInput,
        validators=[validate_password]
    )

    confirm_password = forms.CharField(
        widget=forms.PasswordInput
    )

    def clean_username(self):
        username = self.cleaned_data['username']

        if User.objects.filter(username=username).exists():
            raise forms.ValidationError(
                "This username is already taken."
            )

        return username

    def clean_email(self):
        email = self.cleaned_data['email']

        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                "This email is already registered."
            )

        if Patient.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                "A patient profile with this email already exists."
            )

        return email

    def clean(self):
        cleaned_data = super().clean()

        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password and confirm_password:
            if password != confirm_password:
                self.add_error(
                    'confirm_password',
                    "Passwords do not match."
                )

        return cleaned_data




from django import forms
from .models import Consultation


class ConsultationForm(forms.ModelForm):

    class Meta:
        model = Consultation

        fields = [
            'diagnosis',
            'prescription',
            'doctor_notes',
            'advice',
        ]

        widgets = {
            'diagnosis': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Enter diagnosis'
            }),

            'prescription': forms.Textarea(attrs={
                'rows': 5,
                'placeholder':
                'Enter medicine name, strength, dose, '
                'route, frequency and duration'
            }),

            'doctor_notes': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Additional doctor notes'
            }),

            'advice': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Instructions for patient'
            }),
        }

