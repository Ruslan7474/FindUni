from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from applications.models import Application
from core.models import Announcement, Notification
from institutions.models import Institution, Program


class HomePageTests(TestCase):
    def test_homepage_renders_landing_content(self):
        response = self.client.get(reverse('home'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Найди место, где начнётся')
        self.assertContains(response, 'разных стран')
        self.assertContains(response, 'Популярные заведения')
        self.assertContains(response, 'Открыть поиск')
        self.assertContains(response, 'Версия для слабовидящих')
        self.assertContains(response, 'Университет')
        self.assertContains(response, 'Колледж')
        self.assertContains(response, 'Студент')
        self.assertContains(response, 'История поиска')
        self.assertContains(response, 'Чаще всего ищут')
        self.assertContains(response, 'FindUni помогает сделать уверенный выбор')
        self.assertContains(response, 'Выбирай, сравнивай, поступай')
        self.assertContains(response, 'Находите абитуриентов')
        self.assertNotContains(response, 'Без лишней сложности')
        self.assertNotContains(response, 'От поиска до поступления')
        self.assertContains(response, 'Каталог скоро появится')
        self.assertContains(response, '© 2026 FindUni')
        self.assertNotContains(response, '140+')
        self.assertNotContains(response, '350+')
        self.assertNotContains(response, 'Заявление отправлено')
        self.assertNotContains(response, '42 заведения')
        self.assertEqual(response.context['featured_institutions'], [])

    def test_institution_call_to_action_prefills_registration_role(self):
        response = self.client.get(f"{reverse('register')}?role=institution")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['form']['role'].value(), 'institution')

    def test_homepage_search_shows_empty_state(self):
        response = self.client.get(reverse('home'), {'q': 'несуществующее заведение'})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'По вашему запросу ничего не найдено')


class AboutPageTests(TestCase):
    def test_about_counts_institutions_at_registration_and_real_programs(self):
        response = self.client.post(reverse('register'), {
            'name': 'Колледж для счётчика',
            'email': 'counter-college@example.com',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!',
            'role': 'institution',
        })
        self.assertEqual(response.status_code, 302)
        institution = Institution.objects.get(name='Колледж для счётчика')
        Program.objects.create(institution=institution, name='Программа для счётчика')

        response = self.client.get(reverse('about'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['institution_count'], 1)
        self.assertEqual(response.context['program_count'], 1)
        self.assertNotContains(response, '140+')
        self.assertNotContains(response, '350+')
        self.assertNotContains(response, '100%')


class FooterLinkTests(TestCase):
    def test_footer_links_only_point_to_existing_pages(self):
        response = self.client.get(reverse('student-list'))

        self.assertContains(response, 'href="/about/#faq">Вопросы и ответы</a>')
        self.assertContains(response, 'href="/how-to-apply/">Как поступить</a>')
        self.assertContains(response, 'href="/about/">О нас</a>')
        self.assertNotContains(response, 'Контакты')
        self.assertNotContains(response, 'Конфиденциальность')
        self.assertNotContains(response, 'Условия')

    def test_navigation_mail_button_opens_inbox_and_shows_unread_count(self):
        user = get_user_model().objects.create_user(username='mail-user', password='test-pass', role='student')
        self.client.force_login(user)

        empty_inbox = self.client.get(reverse('home'))

        self.assertContains(empty_inbox, 'data-inbox-open')
        self.assertContains(empty_inbox, 'Сейчас у вас нет почты.')
        self.assertContains(empty_inbox, 'Удалить всю почту')
        self.assertNotContains(empty_inbox, 'footer-mail-button')

        notification = Notification.objects.create(user=user, kind='announcement', title='Плановые работы', body='Обновление платформы')
        populated_inbox = self.client.get(reverse('home'))

        self.assertContains(populated_inbox, 'Плановые работы')
        self.assertContains(populated_inbox, 'Обновление платформы')
        self.assertContains(populated_inbox, 'nav-mail-count')
        self.assertContains(populated_inbox, reverse('notification-mark-read', args=[notification.pk]))
        self.assertContains(populated_inbox, reverse('notification-delete', args=[notification.pk]))

    def test_individual_inbox_actions_are_scoped_to_the_current_user(self):
        user = get_user_model().objects.create_user(username='single-mail-owner', password='test-pass', role='student')
        other_user = get_user_model().objects.create_user(username='single-mail-other', password='test-pass', role='student')
        own_message = Notification.objects.create(user=user, kind='announcement', title='Своё', body='Своё')
        other_message = Notification.objects.create(user=other_user, kind='announcement', title='Чужое', body='Чужое')
        self.client.force_login(user)

        response = self.client.post(reverse('notification-mark-read', args=[other_message.pk]), {'next': '/about/'})

        self.assertRedirects(response, '/about/', fetch_redirect_response=False)
        own_message.refresh_from_db()
        other_message.refresh_from_db()
        self.assertFalse(own_message.is_read)
        self.assertFalse(other_message.is_read)

        self.client.post(reverse('notification-mark-read', args=[own_message.pk]), {'next': '/about/'})
        own_message.refresh_from_db()
        self.assertTrue(own_message.is_read)
        self.client.post(reverse('notification-delete', args=[other_message.pk]), {'next': '/about/'})
        self.assertTrue(Notification.objects.filter(pk=other_message.pk, user=other_user).exists())
        self.client.post(reverse('notification-delete', args=[own_message.pk]), {'next': '/about/'})
        self.assertFalse(Notification.objects.filter(pk=own_message.pk).exists())

    def test_inbox_actions_only_change_the_current_users_messages(self):
        user = get_user_model().objects.create_user(username='mail-owner', password='test-pass', role='student')
        other_user = get_user_model().objects.create_user(username='other-mail-owner', password='test-pass', role='student')
        own_message = Notification.objects.create(user=user, kind='announcement', title='Моё', body='Моё сообщение')
        other_message = Notification.objects.create(user=other_user, kind='announcement', title='Чужое', body='Чужое сообщение')
        self.client.force_login(user)

        response = self.client.post(reverse('inbox-mark-read'), {'next': '/about/?faq=1'})

        self.assertRedirects(response, '/about/?faq=1', fetch_redirect_response=False)
        own_message.refresh_from_db()
        other_message.refresh_from_db()
        self.assertTrue(own_message.is_read)
        self.assertFalse(other_message.is_read)

        self.client.post(reverse('inbox-delete-all'), {'next': '/about/'})

        self.assertFalse(Notification.objects.filter(user=user).exists())
        self.assertTrue(Notification.objects.filter(pk=other_message.pk).exists())

    def test_external_inbox_return_url_is_rejected(self):
        user = get_user_model().objects.create_user(username='safe-mail-user', password='test-pass', role='student')
        self.client.force_login(user)

        response = self.client.post(reverse('inbox-delete-all'), {'next': 'https://example.com/'})

        self.assertRedirects(response, reverse('home'), fetch_redirect_response=False)

    def test_admin_announcement_is_delivered_to_selected_roles_once(self):
        admin = get_user_model().objects.create_superuser(
            username='mail-admin',
            email='mail-admin@example.com',
            password='StrongPass123!',
            role='admin',
        )
        student = get_user_model().objects.create_user(username='announcement-student', password='test-pass', role='student')
        institution_user = get_user_model().objects.create_user(username='announcement-institution', password='test-pass', role='institution')
        self.client.force_login(admin)

        response = self.client.post(reverse('admin:core_announcement_add'), {
            'title': 'Технические работы',
            'body': 'Сервис будет обновлён.',
            'audience': 'student',
            '_save': 'Сохранить',
        })

        self.assertEqual(response.status_code, 302)
        self.assertTrue(Notification.objects.filter(user=student, kind='announcement', title='Технические работы').exists())
        self.assertFalse(Notification.objects.filter(user=institution_user).exists())
        self.assertEqual(Announcement.objects.count(), 1)


class HowToApplyTests(TestCase):
    def test_guest_sees_role_choices(self):
        response = self.client.get(reverse('how-to-apply'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Я абитуриент')
        self.assertContains(response, 'Я учебное заведение')
        self.assertContains(response, '/accounts/register/?role=student')
        self.assertContains(response, '/accounts/register/?role=institution')

    def test_student_sees_admissions_instructions(self):
        user = get_user_model().objects.create_user(username='applicant', password='test-pass', role='student')
        self.client.force_login(user)

        response = self.client.get(reverse('how-to-apply'))

        self.assertContains(response, 'Заполни профиль')
        self.assertContains(response, '/applications/submit/')
        self.assertContains(response, '/applications/dashboard/')

    def test_institution_sees_recruitment_instructions(self):
        user = get_user_model().objects.create_user(username='institution', password='test-pass', role='institution')
        self.client.force_login(user)

        response = self.client.get(reverse('how-to-apply'))

        self.assertContains(response, 'Как принимать абитуриентов')
        self.assertContains(response, 'Рассматривай заявления')
        self.assertContains(response, '/applications/dashboard/')


class AccessibilityToggleTests(TestCase):
    def test_accessibility_control_exposes_clear_on_and_off_states(self):
        inactive = self.client.get(reverse('about'))
        self.assertContains(inactive, 'Включить увеличенный текст')
        self.assertContains(inactive, 'Крупный текст')

        active = self.client.get(reverse('about'), HTTP_COOKIE='large_text=1')
        self.assertContains(active, 'Выключить увеличенный текст')
        self.assertContains(active, 'Текст увеличен')
        self.assertContains(active, 'accessibility-active-indicator')

    def test_enabling_accessibility_returns_to_current_page_and_persists(self):
        response = self.client.get(reverse('large-text-switch'), {'next': '/students/?q=anna'})

        self.assertRedirects(response, '/students/?q=anna', fetch_redirect_response=False)
        self.assertEqual(response.cookies['large_text'].value, '1')
        self.assertEqual(int(response.cookies['large_text']['max-age']), 60 * 60 * 24 * 365)
        self.assertEqual(response.cookies['large_text']['path'], '/')
        next_page = self.client.get('/about/')
        self.assertContains(next_page, 'large-text')

    def test_disabling_accessibility_returns_to_current_page(self):
        self.client.cookies['large_text'] = '1'

        response = self.client.get(reverse('large-text-switch'), {'next': '/about/'})

        self.assertRedirects(response, '/about/', fetch_redirect_response=False)
        self.assertEqual(response.cookies['large_text'].value, '')
        self.assertEqual(response.cookies['large_text']['max-age'], 0)

    def test_external_return_url_is_rejected(self):
        response = self.client.get(reverse('large-text-switch'), {'next': 'https://example.com/'})

        self.assertRedirects(response, reverse('home'), fetch_redirect_response=False)


class ThemeToggleTests(TestCase):
    def test_theme_switch_preserves_current_url_and_persists(self):
        response = self.client.get(reverse('theme-switch', args=['dark']), {'next': '/institutions/?sort=price'})

        self.assertRedirects(response, '/institutions/?sort=price', fetch_redirect_response=False)
        self.assertEqual(response.cookies['theme'].value, 'dark')
        self.assertEqual(int(response.cookies['theme']['max-age']), 60 * 60 * 24 * 365)

    def test_theme_switch_rejects_external_return_url(self):
        response = self.client.get(reverse('theme-switch', args=['light']), {'next': 'https://example.com/'})

        self.assertRedirects(response, reverse('home'), fetch_redirect_response=False)


class DemoDataCommandTests(TestCase):
    def test_command_is_idempotent(self):
        call_command('create_demo_data')
        first_counts = {
            'users': get_user_model().objects.count(),
            'institutions': Institution.objects.count(),
            'programs': Program.objects.count(),
            'applications': Application.objects.count(),
        }
        call_command('create_demo_data')
        self.assertEqual(get_user_model().objects.count(), first_counts['users'])
        self.assertEqual(Institution.objects.count(), first_counts['institutions'])
        self.assertEqual(Program.objects.count(), first_counts['programs'])
        self.assertEqual(Application.objects.count(), first_counts['applications'])
