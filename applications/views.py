from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import FileResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.db import transaction
from applications.forms import ApplicationForm, validate_application_document
from applications.models import Application, ApplicationDocument
from core.models import Notification
from institutions.models import Program
from students.models import StudentProfile

@login_required
def submit_application(request):
    if request.user.role != 'student':
        return redirect('home')
    document_errors = {}
    if request.method == 'POST':
        form = ApplicationForm(request.POST, student=request.user)
        if form.is_valid():
            requirements = list(form.cleaned_data['program'].document_requirements.all())
            uploads = []
            for requirement in requirements:
                upload = request.FILES.get(f'document_{requirement.pk}')
                if not upload:
                    if requirement.is_required:
                        document_errors[requirement.pk] = 'Приложите этот документ.'
                    continue
                try:
                    validate_application_document(upload, requirement)
                except ValidationError as error:
                    document_errors[requirement.pk] = error.messages[0]
                else:
                    uploads.append((requirement, upload))
            if not document_errors:
                with transaction.atomic():
                    application = form.save(commit=False)
                    application.student = request.user
                    application.status = 'sent'
                    StudentProfile.objects.get_or_create(
                        user=request.user,
                        defaults={'full_name': request.user.get_full_name()},
                    )
                    application.save()
                    for requirement, upload in uploads:
                        ApplicationDocument.objects.create(
                            application=application,
                            requirement=requirement,
                            name=requirement.name,
                            file_format=requirement.file_format,
                            file=upload,
                        )
                    Notification.objects.create(
                        user=application.institution.owner,
                        kind='application',
                        title='Новое заявление',
                        body=f'{application.student.get_full_name() or "Абитуриент"} подал заявление на программу «{application.program.name}».',
                        application=application,
                        actor=application.student,
                    )
                return redirect('application-dashboard')
    else:
        initial = {
            key: request.GET[key]
            for key in ('institution', 'program')
            if request.GET.get(key)
        }
        form = ApplicationForm(student=request.user, initial=initial)

    selected_program = None
    program_id = request.POST.get('program') or request.GET.get('program')
    institution_id = request.POST.get('institution') or request.GET.get('institution')
    if program_id and institution_id:
        selected_program = Program.objects.filter(
            pk=program_id,
            institution_id=institution_id,
            institution__approved=True,
        ).first()
    requirements = selected_program.document_requirements.all() if selected_program else []
    document_fields = [
        {'requirement': requirement, 'error': document_errors.get(requirement.pk, '')}
        for requirement in requirements
    ]
    return render(request, 'applications/submit.html', {
        'form': form,
        'selected_program': selected_program,
        'document_fields': document_fields,
        'max_document_size_mb': 10,
    })


@login_required
def program_document_requirements_json(request, pk):
    if request.user.role != 'student':
        raise PermissionDenied
    program = get_object_or_404(Program, pk=pk, institution__approved=True)
    return JsonResponse({
        'requirements': [
            {
                'id': requirement.pk,
                'name': requirement.name,
                'format': requirement.file_format,
                'format_label': requirement.get_file_format_display(),
                'required': requirement.is_required,
            }
            for requirement in program.document_requirements.all()
        ],
    })

@login_required
def application_dashboard(request):
    if request.user.role == 'student':
        applications = request.user.applications.select_related('institution', 'program').prefetch_related('documents').all()
    elif request.user.role == 'institution':
        applications = Application.objects.filter(institution__owner=request.user).select_related('student', 'program').prefetch_related('documents').all()
    else:
        applications = Application.objects.select_related('student', 'institution', 'program').prefetch_related('documents').all()
    return render(request, 'applications/dashboard.html', {'applications': applications})


@login_required
def application_detail(request, pk):
    application = get_object_or_404(
        Application.objects.select_related('student', 'institution', 'program').prefetch_related('documents'),
        pk=pk,
    )
    is_admin = request.user.role == 'admin' or request.user.is_superuser
    can_view = (
        is_admin
        or application.student_id == request.user.pk
        or (request.user.role == 'institution' and application.institution.owner_id == request.user.pk)
    )
    if not can_view:
        raise PermissionDenied
    profile = StudentProfile.objects.filter(user=application.student).first()
    applicant_name = (
        profile.full_name if profile and profile.full_name
        else application.student.get_full_name()
        or 'Абитуриент'
    )
    return render(request, 'applications/detail.html', {
        'application': application,
        'student_profile': profile,
        'applicant_name': applicant_name,
        'can_update_status': request.user.role == 'institution' and application.institution.owner_id == request.user.pk,
    })


@login_required
def download_application_document(request, pk):
    document = get_object_or_404(
        ApplicationDocument.objects.select_related('application__institution', 'application__student'),
        pk=pk,
    )
    application = document.application
    is_admin = request.user.role == 'admin' or request.user.is_superuser
    can_view = (
        is_admin
        or application.student_id == request.user.pk
        or (request.user.role == 'institution' and application.institution.owner_id == request.user.pk)
    )
    if not can_view:
        raise PermissionDenied
    content_types = {'jpg': 'image/jpeg', 'png': 'image/png', 'pdf': 'application/pdf'}
    return FileResponse(
        document.file.open('rb'),
        as_attachment=True,
        filename=f'application-document-{document.pk}.{document.file_format}',
        content_type=content_types[document.file_format],
    )

@login_required
def update_application_status(request, pk):
    application = get_object_or_404(Application, pk=pk)
    if request.user.role != 'institution' or application.institution.owner_id != request.user.pk:
        raise PermissionDenied
    if request.method == 'POST':
        status = request.POST.get('status')
        if status in {'reviewing', 'documents', 'accepted', 'rejected'}:
            previous_status = application.status
            with transaction.atomic():
                application.status = status
                application.save(update_fields=['status', 'updated_at'])
                if status != previous_status and status in {'accepted', 'rejected'}:
                    status_label = application.get_status_display()
                    body = (
                        f'Учебное заведение «{application.institution.name}» обновило статус '
                        f'вашего заявления на программу «{application.program.name}»: {status_label}.'
                    )
                    if status == 'rejected' and application.rejection_reason:
                        body = f'{body} Причина: {application.rejection_reason}'
                    Notification.objects.create(
                        user=application.student,
                        kind='application_status',
                        title=f'Заявление {status_label.lower()}',
                        body=body,
                        application=application,
                        actor=application.institution.owner,
                    )
    return redirect('application-dashboard')
