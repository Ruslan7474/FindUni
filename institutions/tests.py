from io import BytesIO
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from PIL import Image
from core.models import Notification
from institutions.models import Institution, InstitutionPhoto, Program, ProgramDocumentRequirement, Review
from students.models import InstitutionFollow, StudentProfile


class InstitutionSearchTests(TestCase):
    def setUp(self):
        moscow_owner = get_user_model().objects.create_user(username='moscow-owner', password='Pass123!', role='institution')
        spb_owner = get_user_model().objects.create_user(username='spb-owner', password='Pass123!', role='institution')
        self.moscow = Institution.objects.create(
            owner=moscow_owner, name='Московский вуз', institution_type='university', city='Москва', approved=True, rating=4.5
        )
        Program.objects.create(institution=self.moscow, name='Программирование', price=12000)
        self.spb = Institution.objects.create(
            owner=spb_owner, name='Санкт-Петербургский вуз', institution_type='university', city='Санкт-Петербург', approved=True, rating=4.2
        )
        Program.objects.create(institution=self.spb, name='Бизнес', price=8000)

    def test_filters_by_city_and_max_price(self):
        response = self.client.get(reverse('institution-list'), {'city': 'Москва', 'max_price': '15000'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Московский вуз')
        self.assertNotContains(response, 'Санкт-Петербургский вуз')

    def test_direction_filter_matches_program_direction(self):
        Program.objects.create(institution=self.moscow, name='Информационные системы', direction='Информатика')

        response = self.client.get(reverse('institution-list'), {'direction': 'Информатика'})

        self.assertContains(response, self.moscow.name)
        self.assertNotContains(response, self.spb.name)

    def test_sort_by_rating(self):
        response = self.client.get(reverse('institution-list'), {'sort': 'rating'})
        content = response.content.decode('utf-8')
        self.assertIn('Московский вуз', content)
        self.assertLess(content.find('Московский вуз'), content.find('Санкт-Петербургский вуз'))

    def test_filter_controls_use_styled_menus_and_keep_selected_values(self):
        response = self.client.get(reverse('institution-list'), {
            'q': 'технический',
            'city': 'Москва',
            'type': 'university',
            'sort': 'price',
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'institution-filters')
        self.assertContains(response, 'name="city" value="Москва"')
        self.assertContains(response, 'name="type" value="university"')
        self.assertContains(response, 'name="sort" value="price"')

    def test_institution_list_paginates_ten_and_keeps_filters(self):
        for index in range(11):
            owner = get_user_model().objects.create_user(
                username=f'page-institution-{index}',
                password='Pass123!',
                role='institution',
            )
            Institution.objects.create(
                owner=owner,
                name=f'Пагинация колледж {index}',
                institution_type='college9',
                city='Бишкек',
                approved=True,
            )

        filters = {'q': 'Пагинация', 'city': 'Бишкек', 'type': 'college9'}
        first_page = self.client.get(reverse('institution-list'), filters)

        self.assertEqual(first_page.context['page_obj'].paginator.per_page, 10)
        self.assertEqual(len(first_page.context['institutions']), 10)
        self.assertContains(first_page, 'page=2')

        second_page = self.client.get(reverse('institution-list'), {**filters, 'page': '2'})

        self.assertEqual(len(second_page.context['institutions']), 1)
        self.assertEqual(second_page.context['institutions'][0].name, 'Пагинация колледж 10')

    def test_institution_list_card_uses_uploaded_logo(self):
        self.moscow.logo = 'logos/moscow-campus.jpg'
        self.moscow.save(update_fields=['logo'])

        response = self.client.get(reverse('institution-list'))

        self.assertContains(response, '/media/logos/moscow-campus.jpg')

    def test_institution_owner_can_open_unpublished_profile(self):
        owner = get_user_model().objects.create_user(username='private-owner', password='Pass123!', role='institution')
        institution = Institution.objects.create(owner=owner, name='Профиль на модерации')
        self.client.force_login(owner)

        response = self.client.get(reverse('institution-profile'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Профиль на модерации')
        self.assertContains(response, 'Страница не опубликована')
        self.assertContains(response, reverse('dashboard'))
        self.assertContains(response, 'Учебные программы пока не добавлены.')
        self.assertContains(response, 'Добавить направление / программу')
        self.assertContains(response, 'Грантовые места')

    def test_new_program_leads_owner_to_document_requirement_setup(self):
        self.client.force_login(self.moscow.owner)

        response = self.client.post(reverse('institution-profile'), {
            'programs-TOTAL_FORMS': '1',
            'programs-INITIAL_FORMS': '0',
            'programs-MIN_NUM_FORMS': '0',
            'programs-MAX_NUM_FORMS': '1000',
            'programs-0-name': 'Прикладная математика',
            'programs-0-direction': 'Математика',
            'programs-0-language': 'Русский',
            'programs-0-form': 'Очная',
            'programs-0-duration': '4 года',
            'programs-0-places': '10',
            'programs-0-grant_places': '2',
            'programs-0-price': '0',
        })

        program = Program.objects.get(institution=self.moscow, name='Прикладная математика')
        self.assertRedirects(response, reverse('program-document-requirements', args=[program.pk]))

        response = self.client.post(reverse('program-document-requirements', args=[program.pk]), {
            'requirements-TOTAL_FORMS': '1',
            'requirements-INITIAL_FORMS': '0',
            'requirements-MIN_NUM_FORMS': '0',
            'requirements-MAX_NUM_FORMS': '100',
            'requirements-0-name': 'Фото абитуриента',
            'requirements-0-file_format': 'jpg',
            'requirements-0-is_required': 'on',
        })

        self.assertRedirects(response, reverse('institution-profile'))
        self.assertTrue(ProgramDocumentRequirement.objects.filter(
            program=program,
            name='Фото абитуриента',
            file_format='jpg',
            is_required=True,
        ).exists())

    def test_only_program_owner_can_manage_document_requirements(self):
        program = Program.objects.create(institution=self.moscow, name='Защищённая программа')
        other_owner = get_user_model().objects.create_user(
            username='requirements-outsider',
            password='Pass123!',
            role='institution',
        )
        self.client.force_login(other_owner)

        response = self.client.get(reverse('program-document-requirements', args=[program.pk]))

        self.assertEqual(response.status_code, 404)

    def test_student_cannot_open_institution_owner_profile(self):
        student = get_user_model().objects.create_user(username='profile-reader', password='Pass123!', role='student')
        self.client.force_login(student)

        response = self.client.get(reverse('institution-profile'))

        self.assertEqual(response.status_code, 403)

        response = self.client.post(reverse('institution-profile'), {'programs-TOTAL_FORMS': '1'})
        self.assertEqual(response.status_code, 403)

    def test_public_institution_page_uses_real_records_without_demo_statistics(self):
        Program.objects.filter(institution=self.moscow, name='Программирование').update(grant_places=5)
        response = self.client.get(reverse('institution-detail', args=[self.moscow.pk]))

        self.assertContains(response, self.moscow.name)
        self.assertContains(response, 'Программирование')
        self.assertContains(response, 'Грантовых мест: 5')
        self.assertNotContains(response, 'Добавить направление / программу')
        self.assertNotContains(response, '12 500+')
        self.assertNotContains(response, '18 международных партнёров')

    def test_review_saves_and_refreshes_institution_rating(self):
        student = get_user_model().objects.create_user(username='rating-student', password='Pass123!', role='student')

        first_review = Review.objects.create(institution=self.moscow, author=student, rating=5, text='Отлично')
        self.moscow.refresh_from_db()
        self.assertEqual(self.moscow.rating, 5)
        self.assertEqual(self.moscow.rating_count, 1)

        Review.objects.create(institution=self.moscow, author=student, rating=3, text='Нормально')
        self.moscow.refresh_from_db()
        self.assertEqual(self.moscow.rating, 4)
        self.assertEqual(self.moscow.rating_count, 2)

        first_review.is_removed = True
        first_review.save()
        self.moscow.refresh_from_db()
        self.assertEqual(self.moscow.rating, 3)
        self.assertEqual(self.moscow.rating_count, 1)

    def test_student_can_submit_review_and_see_updated_rating(self):
        student = get_user_model().objects.create_user(username='review-author', password='Pass123!', role='student')
        self.client.force_login(student)

        response = self.client.post(reverse('add-review', args=[self.moscow.pk]), {
            'rating': '4',
            'text': 'Полезная программа',
        })

        self.assertRedirects(response, reverse('institution-detail', args=[self.moscow.pk]))
        self.moscow.refresh_from_db()
        self.assertEqual(self.moscow.rating, 4)
        self.assertEqual(self.moscow.rating_count, 1)

    def test_home_card_uses_uploaded_photo_and_real_direction_count(self):
        InstitutionPhoto.objects.create(institution=self.moscow, image='institution-photos/campus.jpg')
        Program.objects.create(institution=self.moscow, name='Разработка', direction='Информатика')
        Program.objects.create(institution=self.moscow, name='Сети', direction='Информатика')
        Program.objects.create(institution=self.moscow, name='Экономика', direction='Экономика')

        response = self.client.get(reverse('home'))

        self.assertContains(response, '/media/institution-photos/campus.jpg')
        self.assertContains(response, '2 направлений')
        self.assertNotContains(response, '3 направлений')

    def test_institution_owner_adds_program_on_profile_and_photo_in_dashboard(self):
        owner = self.moscow.owner
        self.client.force_login(owner)
        image_buffer = BytesIO()
        Image.new('RGB', (1, 1), color='white').save(image_buffer, format='PNG')

        response = self.client.post(reverse('institution-profile'), {
            'programs-TOTAL_FORMS': '1',
            'programs-INITIAL_FORMS': '0',
            'programs-MIN_NUM_FORMS': '0',
            'programs-MAX_NUM_FORMS': '1000',
            'programs-0-name': 'Информационные системы',
            'programs-0-direction': 'Информатика',
            'programs-0-language': 'Русский',
            'programs-0-form': 'Очная',
            'programs-0-duration': '4 года',
            'programs-0-places': '20',
            'programs-0-grant_places': '5',
            'programs-0-price': '10000',
        })

        program = Program.objects.get(
            institution=self.moscow,
            name='Информационные системы',
            direction='Информатика',
        )
        self.assertRedirects(response, reverse('program-document-requirements', args=[program.pk]))
        self.assertEqual(program.places, 20)
        self.assertEqual(program.grant_places, 5)

        response = self.client.post(reverse('dashboard'), {
            'profile_type': 'institution',
            'name': self.moscow.name,
            'institution_type': self.moscow.institution_type,
            'city': self.moscow.city,
            'photos-TOTAL_FORMS': '1',
            'photos-INITIAL_FORMS': '0',
            'photos-MIN_NUM_FORMS': '0',
            'photos-MAX_NUM_FORMS': '1000',
            'photos-0-image': SimpleUploadedFile('campus.png', image_buffer.getvalue(), content_type='image/png'),
        })

        self.assertRedirects(response, reverse('dashboard'))
        self.assertTrue(InstitutionPhoto.objects.filter(institution=self.moscow).exists())
        dashboard = self.client.get(reverse('dashboard'))
        self.assertNotContains(dashboard, 'Добавить направление / программу')
        self.assertNotContains(dashboard, 'programs-TOTAL_FORMS')

    def test_institution_owner_can_update_and_delete_program_from_profile(self):
        owner = self.moscow.owner
        Program.objects.filter(institution=self.moscow).delete()
        program = Program.objects.create(
            institution=self.moscow,
            name='Старая программа',
            direction='Информатика',
            grant_places=2,
        )
        self.client.force_login(owner)

        response = self.client.post(reverse('institution-profile'), {
            'programs-TOTAL_FORMS': '1',
            'programs-INITIAL_FORMS': '1',
            'programs-MIN_NUM_FORMS': '0',
            'programs-MAX_NUM_FORMS': '1000',
            'programs-0-id': str(program.pk),
            'programs-0-institution': str(self.moscow.pk),
            'programs-0-name': 'Новая программа',
            'programs-0-direction': 'Информатика',
            'programs-0-language': 'Русский',
            'programs-0-form': 'Очная',
            'programs-0-duration': '4 года',
            'programs-0-places': '20',
            'programs-0-grant_places': '7',
            'programs-0-price': '10000',
            'programs-0-DELETE': 'on',
        })

        self.assertRedirects(response, reverse('institution-profile'))
        self.assertFalse(Program.objects.filter(pk=program.pk).exists())

    def test_student_can_follow_and_unfollow_institution(self):
        student = get_user_model().objects.create_user(username='institution-follower', password='Pass123!', role='student')
        self.client.force_login(student)
        follow_url = reverse('toggle-institution-follow', args=[self.moscow.pk])

        response = self.client.post(follow_url)

        self.assertRedirects(response, reverse('institution-detail', args=[self.moscow.pk]))
        self.assertTrue(InstitutionFollow.objects.filter(student=student, institution=self.moscow).exists())
        self.assertContains(self.client.get(reverse('institution-detail', args=[self.moscow.pk])), 'Отписаться от заведения')

        self.client.post(follow_url)
        self.assertFalse(InstitutionFollow.objects.filter(student=student, institution=self.moscow).exists())

    def test_institution_follow_requires_student_and_approved_institution(self):
        self.client.force_login(self.moscow.owner)
        response = self.client.post(reverse('toggle-institution-follow', args=[self.moscow.pk]))
        self.assertEqual(response.status_code, 403)

        student = get_user_model().objects.create_user(username='follow-private', password='Pass123!', role='student')
        self.client.force_login(student)
        pending = Institution.objects.create(
            owner=get_user_model().objects.create_user(username='pending-follow-owner', password='Pass123!', role='institution'),
            name='Неодобренное заведение',
        )
        response = self.client.post(reverse('toggle-institution-follow', args=[pending.pk]))
        self.assertEqual(response.status_code, 404)

    def test_student_can_follow_and_unfollow_approved_institution(self):
        student = get_user_model().objects.create_user(username='follow-approved', password='Pass123!', role='student')
        student_profile = StudentProfile.objects.create(user=student, full_name='Подписчик')
        self.client.force_login(student)
        follow_url = reverse('toggle-institution-follow', args=[self.moscow.pk])

        response = self.client.post(follow_url)

        self.assertRedirects(response, reverse('institution-detail', args=[self.moscow.pk]))
        follow = InstitutionFollow.objects.get(student=student, institution=self.moscow)
        follow_notice = Notification.objects.get(user=self.moscow.owner, follow=follow)
        self.assertEqual(follow_notice.actor, student)
        self.assertEqual(follow_notice.kind, 'institution_follow')
        self.assertContains(self.client.get(reverse('institution-detail', args=[self.moscow.pk])), 'Отписаться от заведения')
        self.client.force_login(self.moscow.owner)
        inbox = self.client.get(reverse('home'))
        self.assertContains(inbox, student_profile.full_name)
        self.assertContains(inbox, 'Посмотреть профиль абитуриента')

        self.client.force_login(student)
        self.client.post(follow_url)
        self.assertFalse(InstitutionFollow.objects.filter(student=student, institution=self.moscow).exists())
        self.assertFalse(Notification.objects.filter(pk=follow_notice.pk).exists())

    def test_unapproved_institution_owner_returns_to_dashboard_after_edit(self):
        owner = get_user_model().objects.create_user(username='pending-owner', password='Pass123!', role='institution')
        institution = Institution.objects.create(owner=owner, name='Новое заведение')
        self.client.force_login(owner)

        response = self.client.post(reverse('edit-institution', args=[institution.pk]), {
            'name': 'Новое заведение',
            'institution_type': 'university',
            'city': 'Ош',
        })

        self.assertRedirects(response, reverse('dashboard'))
