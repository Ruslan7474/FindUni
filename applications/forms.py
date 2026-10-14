from django import forms
from django.core.exceptions import ValidationError
from pathlib import Path
from .models import Application

MAX_APPLICATION_DOCUMENT_SIZE = 10 * 1024 * 1024


def validate_application_document(upload, requirement):
    if upload.size > MAX_APPLICATION_DOCUMENT_SIZE:
        raise ValidationError('Размер файла не должен превышать 10 МБ.')

    extension = Path(upload.name).suffix.lower()
    allowed_extensions = {
        'jpg': {'.jpg', '.jpeg'},
        'png': {'.png'},
        'pdf': {'.pdf'},
    }
    if extension not in allowed_extensions[requirement.file_format]:
        raise ValidationError(f'Для документа «{requirement.name}» требуется формат {requirement.get_file_format_display()}.')

    signature = upload.read(8)
    upload.seek(0)
    valid_signature = {
        'jpg': signature.startswith(b'\xff\xd8\xff'),
        'png': signature.startswith(b'\x89PNG\r\n\x1a\n'),
        'pdf': signature.startswith(b'%PDF-'),
    }[requirement.file_format]
    if not valid_signature:
        raise ValidationError('Содержимое файла не соответствует выбранному формату.')

class ApplicationForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ('institution', 'program', 'message')

    def __init__(self, *args, student, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['institution'].queryset = self.fields['institution'].queryset.filter(approved=True)
        self.fields['program'].queryset = self.fields['program'].queryset.filter(institution__approved=True)
        self.student = student

    def clean(self):
        cleaned = super().clean()
        institution = cleaned.get('institution')
        program = cleaned.get('program')
        if institution and program and program.institution_id != institution.pk:
            self.add_error('program', 'Программа должна относиться к выбранному заведению.')
        if institution and Application.objects.filter(student=self.student, institution=institution, program=program).exists():
            self.add_error('program', 'Заявка на эту программу уже отправлена.')
        return cleaned
