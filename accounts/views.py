from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.shortcuts import redirect, render
from institutions.models import Institution
from institutions.forms import InstitutionForm, InstitutionPhotoFormSet
from students.forms import StudentProfileForm
from students.models import StudentProfile
from .forms import EmailOrUsernameAuthenticationForm, RegistrationForm


def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)
            if user.role == 'institution':
                return redirect('dashboard')
            return redirect('home')
    else:
        role = request.GET.get('role')
        initial = {'role': role} if role in {'student', 'institution'} else None
        form = RegistrationForm(initial=initial)
    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        form = EmailOrUsernameAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            auth_login(request, form.get_user())
            return redirect('home')
    else:
        form = EmailOrUsernameAuthenticationForm(request)
    form.fields['username'].label = 'Email'
    form.fields['password'].label = 'Пароль'
    return render(request, 'accounts/login.html', {'form': form})


@login_required
def logout_view(request):
    auth_logout(request)
    return redirect('home')


@login_required
def dashboard(request):
    institution_profile = None
    student_profile = None
    student_form = None
    institution_form = None
    photo_formset = None
    if request.user.role == 'institution':
        institution_profile, _ = Institution.objects.get_or_create(
            owner=request.user,
            defaults={'name': '', 'institution_type': '', 'city': '', 'email': request.user.email},
        )
        if request.method == 'POST' and request.POST.get('profile_type') == 'institution':
            institution_form = InstitutionForm(request.POST, request.FILES, instance=institution_profile)
            has_photo_forms = 'photos-TOTAL_FORMS' in request.POST
            photo_formset = InstitutionPhotoFormSet(
                request.POST if has_photo_forms else None,
                request.FILES if has_photo_forms else None,
                instance=institution_profile,
                prefix='photos',
            )
            photo_forms_valid = not has_photo_forms or photo_formset.is_valid()
            if institution_form.is_valid() and photo_forms_valid:
                with transaction.atomic():
                    institution_form.save()
                    if has_photo_forms:
                        photo_formset.save()
                messages.success(request, 'Профиль учебного заведения сохранён.')
                return redirect('dashboard')
        else:
            institution_form = InstitutionForm(instance=institution_profile)
            photo_formset = InstitutionPhotoFormSet(instance=institution_profile, prefix='photos')
    elif request.user.role == 'student':
        student_profile, _ = StudentProfile.objects.get_or_create(
            user=request.user,
            defaults={'full_name': request.user.get_full_name()},
        )
        if request.method == 'POST' and request.POST.get('profile_type') == 'student':
            student_form = StudentProfileForm(request.POST, request.FILES, instance=student_profile)
            if student_form.is_valid():
                student_profile = student_form.save()
                name_parts = student_profile.full_name.strip().split(maxsplit=1)
                request.user.first_name = name_parts[0] if name_parts else ''
                request.user.last_name = name_parts[1] if len(name_parts) > 1 else ''
                request.user.save(update_fields=['first_name', 'last_name'])
                messages.success(request, 'Профиль абитуриента сохранён.')
                return redirect('dashboard')
        else:
            student_form = StudentProfileForm(instance=student_profile)
    return render(request, 'accounts/dashboard.html', {
        'institution_profile': institution_profile,
        'student_profile': student_profile,
        'student_form': student_form,
        'institution_form': institution_form,
        'photo_formset': photo_formset,
    })
