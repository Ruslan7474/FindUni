from django.conf import settings
from django.db import models
from django.utils import timezone
from uuid import uuid4
from pathlib import Path
from .storage import PrivateApplicationStorage


def application_document_path(instance, filename):
    extension = Path(filename).suffix.lower()
    return f'application-documents/{uuid4().hex}{extension}'


class Application(models.Model):
    STATUS_CHOICES = [('sent', 'Отправлено'), ('reviewing', 'На рассмотрении'), ('documents', 'Нужны документы'), ('accepted', 'Принято'), ('rejected', 'Отклонено'), ('withdrawn', 'Отозвано')]
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='applications')
    institution = models.ForeignKey('institutions.Institution', on_delete=models.CASCADE, related_name='applications')
    program = models.ForeignKey('institutions.Program', on_delete=models.CASCADE, related_name='applications')
    message = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='sent')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    rejection_reason = models.CharField(max_length=250, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['student', 'institution', 'program'], name='unique_student_program')]
        verbose_name = 'заявление'
        verbose_name_plural = 'заявления'

    def __str__(self):
        return f'{self.student} — {self.program} ({self.get_status_display()})'


class ApplicationDocument(models.Model):
    FORMAT_CHOICES = [('jpg', 'JPG'), ('png', 'PNG'), ('pdf', 'PDF')]
    application = models.ForeignKey(Application, related_name='documents', on_delete=models.CASCADE)
    requirement = models.ForeignKey(
        'institutions.ProgramDocumentRequirement',
        related_name='submitted_documents',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    name = models.CharField(max_length=150)
    file_format = models.CharField(max_length=8, choices=FORMAT_CHOICES)
    file = models.FileField(storage=PrivateApplicationStorage(), upload_to=application_document_path)
    uploaded_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ('pk',)
        verbose_name = 'документ заявления'
        verbose_name_plural = 'документы заявлений'

    def __str__(self):
        return f'{self.application}: {self.name}'
