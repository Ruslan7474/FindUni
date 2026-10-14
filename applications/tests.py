import tempfile
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from applications.models import Application, ApplicationDocument
from applications.storage import PrivateApplicationStorage
from institutions.models import Institution, Program, ProgramDocumentRequirement


class ApplicationTests(TestCase):
    def setUp(self):
        self.student = get_user_model().objects.create_user(
            username='student', password='StrongPass123!', role='student'
        )
        self.institution_owner = get_user_model().objects.create_user(
            username='application-institution-owner', password='StrongPass123!', role='institution'
        )
        self.institution = Institution.objects.create(
            owner=self.institution_owner,
            name='Тестовый вуз',
            institution_type='university',
            city='Москва',
            approved=True,
        )
        self.program = Program.objects.create(
            institution=self.institution,
            name='Программирование',
            price=10000,
        )
        self.private_directory = tempfile.TemporaryDirectory()
        self.document_field = ApplicationDocument._meta.get_field('file')
        self.original_storage = self.document_field.storage
        self.document_field.storage = PrivateApplicationStorage(location=self.private_directory.name)
        self.addCleanup(self.restore_private_storage)

    def restore_private_storage(self):
        self.document_field.storage = self.original_storage
        self.private_directory.cleanup()

    def test_application_is_created_and_visible(self):
        self.client.force_login(self.student)
        response = self.client.post(reverse('submit-application'), {
            'institution': self.institution.pk,
            'program': self.program.pk,
            'message': 'Тест',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Application.objects.filter(student=self.student).exists())
        self.assertContains(self.client.get(reverse('application-dashboard')), 'Программирование')

    def test_duplicate_application_is_rejected(self):
        Application.objects.create(
            student=self.student,
            institution=self.institution,
            program=self.program,
            status='sent',
        )
        self.client.force_login(self.student)
        response = self.client.post(reverse('submit-application'), {
            'institution': self.institution.pk,
            'program': self.program.pk,
            'message': 'Повтор',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Заявка на эту программу уже отправлена.')

    def test_only_institution_owner_can_change_status(self):
        other = get_user_model().objects.create_user(username='other', password='Pass123!', role='institution')
        application = Application.objects.create(
            student=self.student,
            institution=self.institution,
            program=self.program,
            status='sent',
        )
        self.client.force_login(other)
        response = self.client.post(reverse('update-application-status', args=[application.pk]), {'status': 'accepted'})
        self.assertEqual(response.status_code, 403)
        application.refresh_from_db()
        self.assertEqual(application.status, 'sent')

    def test_required_document_must_be_uploaded_before_application(self):
        requirement = ProgramDocumentRequirement.objects.create(
            program=self.program,
            name='Аттестат',
            file_format='pdf',
        )
        self.client.force_login(self.student)

        response = self.client.post(reverse('submit-application'), {
            'institution': self.institution.pk,
            'program': self.program.pk,
            'message': 'Поступаю на программу',
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Приложите этот документ.')
        self.assertFalse(Application.objects.filter(student=self.student).exists())
        self.assertEqual(response.context['document_fields'][0]['requirement'], requirement)

    def test_document_extension_and_signature_are_validated(self):
        requirement = ProgramDocumentRequirement.objects.create(
            program=self.program,
            name='Аттестат',
            file_format='pdf',
        )
        self.client.force_login(self.student)

        response = self.client.post(reverse('submit-application'), {
            'institution': self.institution.pk,
            'program': self.program.pk,
            'message': '',
            f'document_{requirement.pk}': SimpleUploadedFile('wrong.jpg', b'not a PDF', content_type='image/jpeg'),
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'требуется формат PDF')
        self.assertFalse(Application.objects.filter(student=self.student).exists())

    def test_documents_are_private_and_downloadable_only_by_parties(self):
        requirement = ProgramDocumentRequirement.objects.create(
            program=self.program,
            name='Аттестат',
            file_format='pdf',
        )
        self.client.force_login(self.student)

        response = self.client.post(reverse('submit-application'), {
            'institution': self.institution.pk,
            'program': self.program.pk,
            'message': 'Поступаю',
            f'document_{requirement.pk}': SimpleUploadedFile(
                'certificate.pdf',
                b'%PDF-1.4\nTest certificate\n%%EOF',
                content_type='application/pdf',
            ),
        })

        self.assertRedirects(response, reverse('application-dashboard'))
        application = Application.objects.get(student=self.student, program=self.program)
        document = ApplicationDocument.objects.get(application=application, requirement=requirement)
        self.assertTrue(document.file.path.startswith(self.private_directory.name))
        with self.assertRaises(NotImplementedError):
            _ = document.file.url

        download_url = reverse('application-document-download', args=[document.pk])
        student_download = self.client.get(download_url)
        self.assertEqual(student_download.status_code, 200)
        self.assertEqual(b''.join(student_download.streaming_content), b'%PDF-1.4\nTest certificate\n%%EOF')
        student_download.close()

        self.client.force_login(self.institution_owner)
        institution_download = self.client.get(download_url)
        self.assertEqual(institution_download.status_code, 200)
        institution_download.close()

        outsider = get_user_model().objects.create_user(
            username='unrelated-document-reader', password='StrongPass123!', role='institution'
        )
        self.client.force_login(outsider)
        self.assertEqual(self.client.get(download_url).status_code, 403)

    def test_program_document_requirements_endpoint_returns_only_approved_programs(self):
        requirement = ProgramDocumentRequirement.objects.create(
            program=self.program,
            name='Фото',
            file_format='jpg',
        )
        self.client.force_login(self.student)

        response = self.client.get(reverse('program-document-requirements-json', args=[self.program.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['requirements'], [{
            'id': requirement.pk,
            'name': 'Фото',
            'format': 'jpg',
            'format_label': 'JPG',
            'required': True,
        }])
