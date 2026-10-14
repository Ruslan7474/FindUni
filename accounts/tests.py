from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from institutions.forms import InstitutionForm
from students.forms import StudentProfileForm


class AuthenticationTests(TestCase):
    def test_registration_and_login(self):
        response = self.client.post(reverse('register'), {
            'name': 'Айжан',
            'last_name': 'Осмонова',
            'email': 'student@example.com',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!',
            'role': 'student',
        })
        self.assertEqual(response.status_code, 302)
        user = get_user_model().objects.get(email='student@example.com')
        self.assertEqual(user.first_name, 'Айжан')
        self.assertEqual(user.last_name, 'Осмонова')
        self.assertEqual(user.student_profile.full_name, 'Айжан Осмонова')
        self.assertEqual(self.client.get(reverse('dashboard')).status_code, 200)
        self.client.logout()
        response = self.client.post(reverse('login'), {
            'username': 'student@example.com',
            'password': 'StrongPass123!',
        })
        self.assertEqual(response.status_code, 302)

    def test_institution_registration_creates_unapproved_profile(self):
        response = self.client.post(reverse('register'), {
            'name': 'ОшТУ',
            'email': 'university@example.com',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!',
            'role': 'institution',
        })

        self.assertRedirects(response, reverse('dashboard'))
        user = get_user_model().objects.get(email='university@example.com')
        profile = user.institution_profile
        self.assertEqual(profile.name, 'ОшТУ')
        self.assertEqual(profile.email, 'university@example.com')
        self.assertFalse(profile.approved)
        self.assertEqual(profile.city, '')
        self.assertEqual(profile.institution_type, '')
        dashboard = self.client.get(reverse('dashboard'))
        self.assertContains(dashboard, 'Открыть страницу')
        self.assertContains(dashboard, 'name="profile_type" value="institution"')
        self.assertContains(dashboard, 'Название учебного заведения')

    def test_registration_form_has_only_requested_fields_and_role_name(self):
        response = self.client.get(reverse('register'), {'role': 'institution'})
        form = response.context['form']

        self.assertEqual(list(form.fields), ['role', 'name', 'last_name', 'email', 'password1', 'password2'])
        self.assertEqual(form['name'].label, 'Название учебного заведения')
        self.assertFalse(form.fields['last_name'].required)
        self.assertEqual(form['password1'].help_text, '')
        self.assertEqual(form['password2'].help_text, '')

    def test_student_registration_requires_last_name(self):
        response = self.client.post(reverse('register'), {
            'name': 'Айжан',
            'email': 'student@example.com',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!',
            'role': 'student',
        })

        self.assertEqual(response.status_code, 200)
        self.assertIn('last_name', response.context['form'].errors)

    def test_student_can_edit_profile_from_dashboard(self):
        user = get_user_model().objects.create_user(
            username='dashboard-student',
            password='StrongPass123!',
            role='student',
        )
        self.client.force_login(user)

        response = self.client.post(reverse('dashboard'), {
            'profile_type': 'student',
            'full_name': 'Нурлан Абдиев',
            'date_of_birth': '2007-05-12',
            'city': 'Ош',
            'bio': 'Поступаю на инженерную программу.',
        })

        self.assertRedirects(response, reverse('dashboard'))
        user.refresh_from_db()
        self.assertEqual(user.student_profile.full_name, 'Нурлан Абдиев')
        self.assertEqual(user.first_name, 'Нурлан')
        self.assertEqual(user.last_name, 'Абдиев')
        self.assertEqual(user.student_profile.city, 'Ош')

    def test_institution_can_edit_profile_from_dashboard(self):
        user = get_user_model().objects.create_user(
            username='dashboard-institution',
            email='dashboard-institution@example.com',
            password='StrongPass123!',
            role='institution',
        )
        from institutions.models import Institution

        institution = Institution.objects.create(owner=user, name='Учебное заведение')
        self.client.force_login(user)

        response = self.client.post(reverse('dashboard'), {
            'profile_type': 'institution',
            'name': 'Новый колледж',
            'institution_type': 'college9',
            'city': 'Бишкек',
            'address': 'Центральная улица',
            'description': 'Описание заведения',
            'history': '',
            'website': '',
            'phone': '',
            'email': 'admission@example.com',
        })

        self.assertRedirects(response, reverse('dashboard'))
        institution.refresh_from_db()
        self.assertEqual(institution.name, 'Новый колледж')
        self.assertEqual(institution.city, 'Бишкек')
        self.assertFalse(institution.approved)

    def test_profile_edit_forms_use_russian_labels(self):
        student_labels = [field.label for field in StudentProfileForm().fields.values()]
        institution_labels = [field.label for field in InstitutionForm().fields.values()]

        self.assertIn('Имя и фамилия', student_labels)
        self.assertIn('Показывать электронную почту учебным заведениям', student_labels)
        self.assertIn('Электронная почта для абитуриентов', institution_labels)
        self.assertFalse(any('Email' in label for label in student_labels + institution_labels))

    def test_admin_index_uses_finduni_branding_and_russian_labels(self):
        admin_user = get_user_model().objects.create_superuser(
            username='panel-admin',
            email='panel-admin@example.com',
            password='StrongPass123!',
        )
        self.client.force_login(admin_user)

        response = self.client.get(reverse('admin:index'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'FindUni')
        self.assertContains(response, 'Панель управления')
        self.assertContains(response, 'Управление платформой')
        self.assertContains(response, 'Пользователи')
        self.assertContains(response, 'Учебные заведения')
        self.assertContains(response, 'Абитуриенты и профили')

    def test_admin_user_add_form_has_russian_labels_and_help(self):
        admin_user = get_user_model().objects.create_superuser(
            username='panel-form-admin',
            email='panel-form-admin@example.com',
            password='StrongPass123!',
        )
        self.client.force_login(admin_user)

        response = self.client.get(reverse('admin:accounts_user_add'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Роль на платформе')
        self.assertContains(response, 'Подтверждение пароля')
        self.assertContains(response, 'Обязательное поле')
        self.assertNotContains(response, 'Required. 150 characters')

    def test_admin_institution_add_form_has_russian_labels(self):
        admin_user = get_user_model().objects.create_superuser(
            username='panel-institution-admin',
            email='panel-institution-admin@example.com',
            password='StrongPass123!',
        )
        self.client.force_login(admin_user)

        response = self.client.get(reverse('admin:institutions_institution_add'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Название')
        self.assertContains(response, 'Тип заведения')
        self.assertContains(response, 'Одобрено модератором')

    def test_admin_readonly_fields_have_russian_labels(self):
        admin_user = get_user_model().objects.create_superuser(
            username='panel-readonly-admin',
            email='panel-readonly-admin@example.com',
            password='StrongPass123!',
        )
        self.client.force_login(admin_user)

        user_response = self.client.get(reverse('admin:accounts_user_change', args=[admin_user.pk]))
        institution_response = self.client.get(reverse('admin:institutions_institution_add'))
        student_response = self.client.get(reverse('admin:students_studentprofile_add'))
        application_response = self.client.get(reverse('admin:applications_application_add'))

        self.assertContains(user_response, 'Последний вход')
        self.assertContains(user_response, 'Дата регистрации')
        self.assertContains(institution_response, 'Рейтинг')
        self.assertContains(institution_response, 'Количество оценок')
        self.assertContains(institution_response, 'Дата добавления')
        self.assertContains(student_response, 'Дата создания')
        self.assertContains(student_response, 'Последнее изменение')
        self.assertContains(application_response, 'Дата отправки')
        self.assertContains(application_response, 'Последнее изменение')
        self.assertNotContains(institution_response, 'Rating count:')
        self.assertNotContains(student_response, 'Created at:')

    def test_admin_login_is_russian_even_when_browser_language_is_english(self):
        response = self.client.get(reverse('admin:login'), HTTP_ACCEPT_LANGUAGE='en-US,en;q=0.9')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Имя пользователя')
        self.assertContains(response, 'Пароль')
        self.assertContains(response, 'Войти')
        self.assertNotContains(response, 'Log in')

    def test_registration_role_uses_localized_choices(self):
        response = self.client.get(reverse('register'), {'role': 'institution'})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Кем вы будете на FindUni?')
        self.assertContains(response, 'Абитуриент')
        self.assertContains(response, 'Учебное заведение')
        self.assertEqual(response.context['form']['role'].value(), 'institution')

    def test_institution_list_is_public(self):
        response = self.client.get(reverse('institution-list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Заведения')

    def test_logout_uses_post_and_ends_session(self):
        user = get_user_model().objects.create_user(username='logout-user', password='StrongPass123!')
        self.client.force_login(user)

        response = self.client.post(reverse('logout'), {'next': reverse('home')})

        self.assertRedirects(response, reverse('home'))
        self.assertNotIn('_auth_user_id', self.client.session)
