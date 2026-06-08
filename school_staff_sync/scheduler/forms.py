from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from .models import Schedule, Availability, Profile


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'})
    )


class ScheduleForm(forms.ModelForm):
    class Meta:
        model = Schedule
        fields = ['teacher', 'subject', 'date', 'start_time', 'end_time', 'room', 'photo']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'start_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'end_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'teacher': forms.Select(attrs={'class': 'form-select'}),
            'subject': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Mathematics'}),
            'room': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Room 101'}),
            'photo': forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        }
        labels = {
            'photo': 'Session Photo (optional)',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show users with a teacher profile in the teacher dropdown
        self.fields['teacher'].queryset = User.objects.filter(
            profile__role='teacher'
        ).select_related('profile').order_by('first_name', 'username')
        self.fields['teacher'].label_from_instance = lambda u: (
            f"{u.get_full_name() or u.username}"
        )


class AvailabilityForm(forms.ModelForm):
    class Meta:
        model = Availability
        fields = ['is_confirmed', 'comment']
        widgets = {
            'is_confirmed': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'comment': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Optional comment or reason...',
            }),
        }
        labels = {'is_confirmed': 'I confirm I will teach this session'}


class ProfilePhotoForm(forms.ModelForm):
    """Allows any user (admin or teacher) to upload / change their profile photo."""
    class Meta:
        model = Profile
        fields = ['photo']
        widgets = {
            'photo': forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        }
        labels = {'photo': 'Profile Photo'}


class TeacherCreationForm(forms.ModelForm):
    role = forms.ChoiceField(
        choices=Profile.ROLE_CHOICES,
        initial='teacher',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    photo = forms.ImageField(
        required=False,
        widget=forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        label='Profile Photo (optional)'
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email Address'}),
        }