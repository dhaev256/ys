from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordChangeForm
from .models import Profile, Schedule, Availability
from .forms import LoginForm, ScheduleForm, AvailabilityForm, ProfilePhotoForm, TeacherCreationForm


# ── role helpers ──────────────────────────────────────────────────────────────
def is_admin(user):
    return user.is_superuser or (hasattr(user, 'profile') and user.profile.role == 'admin')


def is_teacher(user):
    return hasattr(user, 'profile') and user.profile.role == 'teacher'


# ── auth views ────────────────────────────────────────────────────────────────
def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('home')
    else:
        form = LoginForm()
    return render(request, 'scheduler/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def home(request):
    if is_admin(request.user):
        return redirect('admin_dashboard')
    elif is_teacher(request.user):
        return redirect('teacher_schedule')
    else:
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden(
            "Your account does not have a designated role. Please contact the administrator."
        )


# ── shared: profile photo ─────────────────────────────────────────────────────
@login_required
def update_profile_photo(request):
    """Any logged-in user (admin or teacher) can update their own profile photo."""
    profile, _ = Profile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = ProfilePhotoForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile photo updated successfully.')
            return redirect('home')
    else:
        form = ProfilePhotoForm(instance=profile)
    return render(request, 'scheduler/profile_photo.html', {'form': form})


# ── admin views ───────────────────────────────────────────────────────────────
@login_required
@user_passes_test(is_admin, login_url='home')
def admin_dashboard(request):
    total_teachers = User.objects.filter(profile__role='teacher').count()
    total_schedules = Schedule.objects.count()
    upcoming_schedules = Schedule.objects.filter(date__gte=timezone.now().date()).count()
    total_confirmations = Availability.objects.filter(is_confirmed=True).count()
    recent_schedules = Schedule.objects.select_related('teacher', 'teacher__profile').order_by('-date')[:5]
    context = {
        'total_teachers': total_teachers,
        'total_schedules': total_schedules,
        'upcoming_schedules': upcoming_schedules,
        'total_confirmations': total_confirmations,
        'recent_schedules': recent_schedules,
    }
    return render(request, 'scheduler/admin_dashboard.html', context)


@login_required
@user_passes_test(is_admin, login_url='home')
def schedule_list(request):
    schedules = Schedule.objects.all().select_related('teacher', 'teacher__profile')
    return render(request, 'scheduler/schedule_list.html', {'schedules': schedules})


@login_required
@user_passes_test(is_admin, login_url='home')
def schedule_create(request):
    if request.method == 'POST':
        # request.FILES is required for image uploads
        form = ScheduleForm(request.POST, request.FILES)
        if form.is_valid():
            schedule = form.save()
            Availability.objects.get_or_create(schedule=schedule, teacher=schedule.teacher)
            messages.success(request, 'Schedule created successfully.')
            return redirect('schedule_list')
    else:
        form = ScheduleForm()
    return render(request, 'scheduler/schedule_form.html', {'form': form, 'title': 'Create Schedule'})


@login_required
@user_passes_test(is_admin, login_url='home')
def schedule_update(request, pk):
    schedule = get_object_or_404(Schedule, pk=pk)
    if request.method == 'POST':
        form = ScheduleForm(request.POST, request.FILES, instance=schedule)
        if form.is_valid():
            form.save()
            messages.success(request, 'Schedule updated.')
            return redirect('schedule_list')
    else:
        form = ScheduleForm(instance=schedule)
    return render(request, 'scheduler/schedule_form.html', {'form': form, 'title': 'Edit Schedule'})


@login_required
@user_passes_test(is_admin, login_url='home')
def schedule_delete(request, pk):
    schedule = get_object_or_404(Schedule, pk=pk)
    if request.method == 'POST':
        schedule.delete()
        messages.success(request, 'Schedule deleted.')
        return redirect('schedule_list')
    return render(request, 'scheduler/schedule_confirm_delete.html', {'schedule': schedule})


# ── teacher views ─────────────────────────────────────────────────────────────
@login_required
@user_passes_test(is_teacher, login_url='home')
def teacher_schedule(request):
    schedules = Schedule.objects.filter(teacher=request.user).order_by('date', 'start_time')
    for s in schedules:
        s.availability, _ = Availability.objects.get_or_create(schedule=s, teacher=request.user)
    return render(request, 'scheduler/teacher_schedule.html', {'schedules': schedules})


@login_required
@user_passes_test(is_teacher, login_url='home')
def update_availability(request, schedule_pk):
    schedule = get_object_or_404(Schedule, pk=schedule_pk, teacher=request.user)
    availability, _ = Availability.objects.get_or_create(schedule=schedule, teacher=request.user)
    if request.method == 'POST':
        form = AvailabilityForm(request.POST, instance=availability)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your availability has been updated.')
            return redirect('teacher_schedule')
    else:
        form = AvailabilityForm(instance=availability)
    return render(request, 'scheduler/teacher_availability.html', {'form': form, 'schedule': schedule})


# ── admin: teacher management views ───────────────────────────────────────────
@login_required
@user_passes_test(is_admin, login_url='home')
def teacher_list(request):
    teachers = User.objects.select_related('profile').all().order_by('profile__role', 'username')
    return render(request, 'scheduler/teacher_list.html', {'teachers': teachers})


@login_required
@user_passes_test(is_admin, login_url='home')
def teacher_create(request):
    if request.method == 'POST':
        form = TeacherCreationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save(commit=False)
            
            # Generate random password
            import secrets
            import string
            # 8 character temporary password: e.g. Staff@xyz123
            digits = ''.join(secrets.choice(string.digits) for _ in range(3))
            letters = ''.join(secrets.choice(string.ascii_lowercase) for _ in range(3))
            temp_password = f"Staff@{letters}{digits}"
            
            user.set_password(temp_password)
            user.save()
            
            # Since the signal automatically creates a profile, retrieve/update it
            profile = user.profile
            profile.role = form.cleaned_data['role']
            if form.cleaned_data['photo']:
                profile.photo = form.cleaned_data['photo']
            profile.save()
            
            # Save temporary credentials in the session to show on the success page
            request.session['created_teacher'] = {
                'username': user.username,
                'password': temp_password,
                'role': profile.get_role_display(),
                'name': user.get_full_name() or user.username
            }
            
            messages.success(request, f"User {user.username} created successfully.")
            return redirect('teacher_creation_success')
    else:
        form = TeacherCreationForm()
    return render(request, 'scheduler/teacher_form.html', {'form': form, 'title': 'Add New Teacher/Staff'})


@login_required
@user_passes_test(is_admin, login_url='home')
def teacher_creation_success(request):
    teacher_info = request.session.get('created_teacher')
    if not teacher_info:
        # Prevent access if no teacher was just created
        return redirect('teacher_list')
    # Clean up session so it cannot be accessed again
    del request.session['created_teacher']
    return render(request, 'scheduler/teacher_creation_success.html', {'teacher': teacher_info})


@login_required
@user_passes_test(is_admin, login_url='home')
def teacher_delete(request, pk):
    teacher = get_object_or_404(User, pk=pk)
    if teacher == request.user:
        messages.error(request, "You cannot delete yourself.")
        return redirect('teacher_list')
    if request.method == 'POST':
        username = teacher.username
        teacher.delete()
        messages.success(request, f"User {username} has been deleted.")
        return redirect('teacher_list')
    return render(request, 'scheduler/teacher_confirm_delete.html', {'teacher_to_delete': teacher})


# ── general: change password ──────────────────────────────────────────────────
@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Your password was successfully updated!')
            return redirect('home')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'scheduler/change_password.html', {'form': form})