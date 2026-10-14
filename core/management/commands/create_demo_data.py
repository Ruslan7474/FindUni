from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from applications.models import Application
from institutions.models import Institution, Program


class Command(BaseCommand):
    help = 'Создаёт демонстрационные пользователи, заведения и заявки.'

    def handle(self, *args, **options):
        User = get_user_model()
        students = []
        for username, first_name, last_name, email in [
            ('student-demo', 'Дмитрий', 'Иванов', 'student@example.com'),
            ('student-demo-2', 'Алина', 'Казакова', 'student2@example.com'),
        ]:
            student, created = User.objects.get_or_create(username=username, defaults={
                'first_name': first_name,
                'last_name': last_name,
                'email': email,
                'role': 'student',
            })
            if created:
                student.set_password('DemoPass123!')
                student.save(update_fields=['password'])
            students.append(student)

        for username, name, city, institution_type, rating in [
            ('institution-demo', 'МосковскийIT-колледж', 'Москва', 'college11', 4.8),
            ('institution-demo-2', 'Санкт-Петербургский университет', 'Санкт-Петербург', 'university', 4.6),
        ]:
            owner, created = User.objects.get_or_create(username=username, defaults={
                'email': f'{username}@example.com',
                'role': 'institution',
            })
            if created:
                owner.set_password('DemoPass123!')
                owner.save(update_fields=['password'])
            institution, _ = Institution.objects.get_or_create(
                owner=owner,
                defaults={
                    'name': name,
                    'institution_type': institution_type,
                    'city': city,
                    'description': 'Демонстрационное учебное заведение.',
                    'approved': True,
                    'rating': rating,
                },
            )
            Program.objects.get_or_create(
                institution=institution,
                name='Программирование',
                defaults={'language': 'Русский', 'form': 'Очная', 'duration': '2 года', 'places': 30, 'price': 15000},
            )

        institutions = list(Institution.objects.filter(approved=True).order_by('pk'))
        for index, student in enumerate(students):
            institution = institutions[index % len(institutions)]
            program = institution.programs.first()
            if program:
                Application.objects.get_or_create(
                    student=student,
                    institution=institution,
                    program=program,
                    defaults={'message': 'Демонстрационная заявка', 'status': 'sent'},
                )

        self.stdout.write(self.style.SUCCESS('Демонстрационные данные готовы.'))
