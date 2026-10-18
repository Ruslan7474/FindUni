from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import get_language
from pathlib import Path
from .models import Application

MAX_APPLICATION_DOCUMENT_SIZE = 10 * 1024 * 1024


def validate_application_document(upload, requirement):
    language = get_language()
    if upload.size > MAX_APPLICATION_DOCUMENT_SIZE:
        message = 'File size must not exceed 10 MB.' if language == 'en' else 'Файлдын өлчөмү 10 МБдан ашпашы керек.' if language == 'ky' else 'Размер файла не должен превышать 10 МБ.'
        raise ValidationError(message)

    extension = Path(upload.name).suffix.lower()
    allowed_extensions = {
        'jpg': {'.jpg', '.jpeg'},
        'png': {'.png'},
        'pdf': {'.pdf'},
    }
    if extension not in allowed_extensions[requirement.file_format]:
        if language == 'en':
            message = f'Document "{requirement.name}" must use the {requirement.get_file_format_display()} format.'
        elif language == 'ky':
            message = f'«{requirement.name}» документи үчүн {requirement.get_file_format_display()} форматы талап кылынат.'
        else:
            message = f'Для документа «{requirement.name}» требуется формат {requirement.get_file_format_display()}.'
        raise ValidationError(message)

    signature = upload.read(8)
    upload.seek(0)
    valid_signature = {
        'jpg': signature.startswith(b'\xff\xd8\xff'),
        'png': signature.startswith(b'\x89PNG\r\n\x1a\n'),
        'pdf': signature.startswith(b'%PDF-'),
    }[requirement.file_format]
    if not valid_signature:
        message = 'File contents do not match the selected format.' if language == 'en' else 'Файлдын мазмуну тандалган форматка туура келбейт.' if language == 'ky' else 'Содержимое файла не соответствует выбранному формату.'
        raise ValidationError(message)

class ApplicationForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ('institution', 'program', 'message')

    def __init__(self, *args, student, **kwargs):
        super().__init__(*args, **kwargs)
        language = get_language()
        if language == 'en':
            self.fields['institution'].label = 'Institution'
            self.fields['program'].label = 'Program'
            self.fields['message'].label = 'Message to the institution'
        elif language == 'ky':
            self.fields['institution'].label = 'Окуу жай'
            self.fields['program'].label = 'Программа'
            self.fields['message'].label = 'Окуу жайга билдирүү'
        self.fields['institution'].queryset = self.fields['institution'].queryset.filter(approved=True)
        self.fields['program'].queryset = self.fields['program'].queryset.filter(institution__approved=True)
        self.student = student

    def clean(self):
        cleaned = super().clean()
        institution = cleaned.get('institution')
        program = cleaned.get('program')
        if institution and program and program.institution_id != institution.pk:
            message = 'The program must belong to the selected institution.' if get_language() == 'en' else 'Программа тандалган окуу жайга тиешелүү болушу керек.' if get_language() == 'ky' else 'Программа должна относиться к выбранному заведению.'
            self.add_error('program', message)
        if institution and Application.objects.filter(student=self.student, institution=institution, program=program).exists():
            message = 'You have already applied to this program.' if get_language() == 'en' else 'Бул программага арыз мурун жөнөтүлгөн.' if get_language() == 'ky' else 'Заявка на эту программу уже отправлена.'
            self.add_error('program', message)
        return cleaned
