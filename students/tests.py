from datetime import date

from django.contrib.auth import get_user_model
from django.db.models import Q
from django.test import TestCase
from django.urls import reverse
from applications.models import Application
from institutions.models import Institution, Program
from students.models import AcademicGrade, Comment, CommentVote, EducationEntry, InstitutionFollow, StudentFriendship, StudentProfile, TestScore


class StudentListSearchTests(TestCase):
	def test_search_form_is_styled_and_keeps_query(self):
		response = self.client.get('/students/', {'q': 'alina'})

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, '<title>Абитуриенты — FindUni</title>')
		self.assertContains(response, 'class="student-search-form"')
		self.assertContains(response, 'role="search"')
		self.assertContains(response, 'value="alina"')

	def test_search_matches_registration_first_and_last_name(self):
		from django.contrib.auth import get_user_model
		from students.models import StudentProfile

		user = get_user_model().objects.create_user(
			username='registered-student',
			first_name='Айжан',
			last_name='Осмонова',
			password='StrongPass123!',
			role='student',
		)
		profile = StudentProfile.objects.create(user=user, full_name=user.get_full_name())

		response = self.client.get('/students/', {'q': 'Осмонова'})

		self.assertContains(response, 'Айжан Осмонова')
		self.assertContains(response, f'/students/{profile.pk}/')

	def test_public_applicant_card_shows_avatar_city_interests_and_education(self):
		from django.contrib.auth import get_user_model
		from students.models import EducationEntry, StudentProfile

		user = get_user_model().objects.create_user(
			username='public-profile-student',
			first_name='Алина',
			last_name='Осмонова',
			password='StrongPass123!',
			role='student',
		)
		profile = StudentProfile.objects.create(
			user=user,
			full_name=user.get_full_name(),
			city='Ош',
			interests='Программирование',
		)
		EducationEntry.objects.create(
			profile=profile,
			level='school',
			institution_name='Публичная школа',
			start_year=2015,
		)

		response = self.client.get('/students/')

		self.assertContains(response, 'Абитуриенты')
		self.assertContains(response, 'Алина Осмонова')
		self.assertContains(response, 'Ош')
		self.assertContains(response, 'Программирование')
		self.assertContains(response, 'Публичная школа')
		self.assertContains(response, 'Открыть профиль')
		self.assertContains(response, 'class="student-card-avatar"')

	def test_student_list_filters_by_city_and_education_institution(self):
		from django.contrib.auth import get_user_model
		from students.models import EducationEntry, StudentProfile

		users = [
			get_user_model().objects.create_user(username='filter-osh', password='StrongPass123!', role='student'),
			get_user_model().objects.create_user(username='filter-bishkek', password='StrongPass123!', role='student'),
		]
		osh_profile = StudentProfile.objects.create(user=users[0], full_name='Ошский абитуриент', city='Ош')
		bishkek_profile = StudentProfile.objects.create(user=users[1], full_name='Бишкекский абитуриент', city='Бишкек')
		EducationEntry.objects.create(profile=osh_profile, level='school', institution_name='Школа № 1', start_year=2018)
		EducationEntry.objects.create(profile=bishkek_profile, level='school', institution_name='Школа № 2', start_year=2018)

		response = self.client.get('/students/', {'city': 'Ош', 'institution': 'Школа № 1'})

		self.assertContains(response, 'Ошский абитуриент')
		self.assertNotContains(response, 'Бишкекский абитуриент')
		self.assertContains(response, 'name="city" value="Ош"')
		self.assertContains(response, 'name="institution" value="Школа № 1"')

	def test_student_list_paginates_ten_and_keeps_search(self):
		for index in range(11):
			user = get_user_model().objects.create_user(
				username=f'paginated-student-{index}',
				password='StrongPass123!',
				role='student',
			)
			StudentProfile.objects.create(user=user, full_name=f'Пагинация абитуриент {index}')

		first_page = self.client.get('/students/', {'q': 'Пагинация'})

		self.assertEqual(first_page.context['page_obj'].paginator.per_page, 10)
		self.assertEqual(len(first_page.context['students']), 10)
		self.assertContains(first_page, 'page=2')

		second_page = self.client.get('/students/', {'q': 'Пагинация', 'page': '2'})

		self.assertEqual(len(second_page.context['students']), 1)
		self.assertEqual(second_page.context['students'][0].full_name, 'Пагинация абитуриент 10')


class StudentCommentInteractionTests(TestCase):
	def setUp(self):
		user_model = get_user_model()
		self.profile_owner = user_model.objects.create_user(
			username='comment-profile-owner',
			password='StrongPass123!',
			role='student',
		)
		self.profile = StudentProfile.objects.create(user=self.profile_owner, full_name='Владелец профиля')
		self.commenter = user_model.objects.create_user(
			username='comment-author',
			password='StrongPass123!',
			role='student',
			first_name='Автор',
			last_name='Комментария',
		)

	def test_comment_and_reply_submit_without_leaving_profile(self):
		self.client.force_login(self.commenter)
		profile_url = reverse('student-detail', args=[self.profile.pk])
		response = self.client.get(profile_url)

		self.assertContains(response, 'id="id_text"')
		self.assertContains(response, 'Напишите комментарий')
		self.assertContains(response, 'class="profile-comment-send"')
		self.assertContains(response, 'aria-label="Отправить комментарий"')
		self.assertContains(response, 'rows="1"')

		response = self.client.post(reverse('add-comment', args=[self.profile.pk]), {'text': 'Первый комментарий'})
		self.assertRedirects(response, f'{profile_url}#comments', fetch_redirect_response=False)
		root = Comment.objects.get(profile=self.profile, text='Первый комментарий')
		self.assertIsNone(root.parent_id)

		response = self.client.post(reverse('add-comment', args=[self.profile.pk]), {
			'text': 'Ответ на комментарий',
			'parent_id': str(root.pk),
		})
		self.assertRedirects(response, f'{profile_url}#comments', fetch_redirect_response=False)
		reply = Comment.objects.get(profile=self.profile, text='Ответ на комментарий')
		self.assertEqual(reply.parent_id, root.pk)

		response = self.client.get(profile_url)
		self.assertContains(response, 'Первый комментарий')
		self.assertContains(response, 'Ответ на комментарий')
		self.assertContains(response, 'Автор Комментария')
		self.assertContains(response, 'profile-comment-avatar')

	def test_comment_votes_toggle_and_switch_between_like_and_dislike(self):
		comment = Comment.objects.create(profile=self.profile, author=self.commenter, text='Комментарий с реакциями')
		voter = get_user_model().objects.create_user(
			username='comment-voter',
			password='StrongPass123!',
			role='student',
		)
		self.client.force_login(voter)
		vote_url = reverse('vote-comment', args=[comment.pk])

		self.client.post(vote_url, {'value': 'like'})
		self.assertEqual(CommentVote.objects.filter(comment=comment, user=voter, value='like').count(), 1)

		self.client.post(vote_url, {'value': 'like'})
		self.assertFalse(CommentVote.objects.filter(comment=comment, user=voter).exists())

		self.client.post(vote_url, {'value': 'dislike'})
		self.client.post(vote_url, {'value': 'like'})
		self.assertEqual(CommentVote.objects.filter(comment=comment, user=voter).count(), 1)
		self.assertTrue(CommentVote.objects.filter(comment=comment, user=voter, value='like').exists())

	def test_ajax_vote_returns_updated_state_as_json(self):
		comment = Comment.objects.create(profile=self.profile, author=self.commenter, text='Комментарий с AJAX-реакцией')
		voter = get_user_model().objects.create_user(
			username='ajax-comment-voter',
			password='StrongPass123!',
			role='student',
		)
		self.client.force_login(voter)
		vote_url = reverse('vote-comment', args=[comment.pk])

		response = self.client.post(vote_url, {'value': 'like'}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.json(), {'like_count': 1, 'dislike_count': 0, 'selected': 'like'})

		response = self.client.post(vote_url, {'value': 'like'}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
		self.assertEqual(response.json(), {'like_count': 0, 'dislike_count': 0, 'selected': None})

	def test_guest_preview_can_read_but_not_interact_with_comments(self):
		Comment.objects.create(profile=self.profile, author=self.commenter, text='Публичный комментарий')

		response = self.client.get(reverse('student-detail', args=[self.profile.pk]), {'view': 'guest'})

		self.assertContains(response, 'Публичный комментарий')
		self.assertNotContains(response, 'Напишите комментарий')
		self.assertNotContains(response, 'Ответить')
		self.assertNotContains(response, 'vote-comment')

	def test_comment_author_fallback_hides_generated_username(self):
		institution_user = get_user_model().objects.create_user(
			username='finduni-generated-uuid',
			password='StrongPass123!',
			role='institution',
		)
		Institution.objects.create(owner=institution_user, name='Колледж автора')
		Comment.objects.create(profile=self.profile, author=institution_user, text='Комментарий учреждения')

		response = self.client.get(reverse('student-detail', args=[self.profile.pk]))

		self.assertContains(response, 'Колледж автора')
		self.assertNotContains(response, 'finduni-generated-uuid')


class StudentProfilePrivacyTests(TestCase):
	def setUp(self):
		user_model = get_user_model()
		self.student = user_model.objects.create_user(
			username='target-student',
			email='private-student@example.com',
			password='StrongPass123!',
			role='student',
			first_name='Айжан',
			last_name='Садыкова',
		)
		self.profile = StudentProfile.objects.create(
			user=self.student,
			full_name='Айжан Садыкова',
			date_of_birth=date(2007, 1, 2),
			city='Ош',
			nationality='Кыргыз',
			citizenship='Кыргызстан',
			bio='Приватное описание профиля',
			email_visible=True,
		)
		self.institution_owner = user_model.objects.create_user(
			username='profile-institution',
			password='StrongPass123!',
			role='institution',
		)
		self.institution = Institution.objects.create(
			owner=self.institution_owner,
			name='Связанный вуз',
			institution_type='university',
			city='Бишкек',
		)
		self.program = Program.objects.create(institution=self.institution, name='Программа')

	def test_guest_cannot_view_private_student_data(self):
		response = self.client.get(reverse('student-detail', args=[self.profile.pk]))

		self.assertFalse(response.context['can_view_full'])
		self.assertNotContains(response, 'Приватное описание профиля')
		self.assertNotContains(response, 'private-student@example.com')
		self.assertNotContains(response, '2007')
		self.assertNotContains(response, 'Ош')
		self.assertNotContains(response, 'Кыргыз</dd>')
		self.assertNotContains(response, 'Кыргызстан</dd>')

	def test_unrelated_student_application_does_not_grant_access(self):
		unrelated_student = get_user_model().objects.create_user(
			username='unrelated-student',
			password='StrongPass123!',
			role='student',
		)
		Application.objects.create(
			student=self.student,
			institution=self.institution,
			program=self.program,
		)
		Application.objects.create(
			student=unrelated_student,
			institution=self.institution,
			program=self.program,
		)
		self.client.force_login(unrelated_student)

		response = self.client.get(reverse('student-detail', args=[self.profile.pk]))

		self.assertFalse(response.context['can_view_full'])
		self.assertNotContains(response, 'Приватное описание профиля')

	def test_related_institution_can_view_full_profile(self):
		Application.objects.create(
			student=self.student,
			institution=self.institution,
			program=self.program,
		)
		self.client.force_login(self.institution_owner)

		response = self.client.get(reverse('student-detail', args=[self.profile.pk]))

		self.assertTrue(response.context['can_view_full'])
		self.assertContains(response, 'Приватное описание профиля')
		self.assertContains(response, 'private-student@example.com')
		self.assertContains(response, 'Кыргыз')
		self.assertContains(response, 'Кыргызстан')

	def test_student_can_view_own_nationality_and_citizenship(self):
		self.client.force_login(self.student)

		response = self.client.get(reverse('student-profile'))

		self.assertContains(response, 'Национальность')
		self.assertContains(response, 'Кыргыз')
		self.assertContains(response, 'Гражданство')
		self.assertContains(response, 'Кыргызстан')

	def test_student_can_edit_nationality_and_citizenship_in_dashboard(self):
		self.client.force_login(self.student)

		response = self.client.post(reverse('dashboard'), {
			'profile_type': 'student',
			'full_name': self.profile.full_name,
			'nationality': 'Узбек',
			'citizenship': 'Кыргызстан',
			'city': 'Ош',
			'date_of_birth': '2007-01-02',
			'bio': self.profile.bio,
		})

		self.assertRedirects(response, reverse('dashboard'))
		self.profile.refresh_from_db()
		self.assertEqual(self.profile.nationality, 'Узбек')
		self.assertEqual(self.profile.citizenship, 'Кыргызстан')

	def test_profile_name_defaults_to_registration_name(self):
		self.client.force_login(self.student)

		response = self.client.get(reverse('student-profile'))

		self.assertEqual(response.context['profile'].full_name, 'Айжан Садыкова')

	def test_guest_preview_hides_private_data_even_for_profile_owner(self):
		self.client.force_login(self.student)

		response = self.client.get(reverse('student-detail', args=[self.profile.pk]), {'view': 'guest'})

		self.assertFalse(response.context['can_view_full'])
		self.assertContains(response, 'Полный профиль закрыт')
		self.assertNotContains(response, 'Приватное описание профиля')
		self.assertNotContains(response, 'private-student@example.com')
		self.assertNotContains(response, '2007')
		self.assertNotContains(response, 'Кабинет')
		self.assertNotContains(response, 'Выйти')
		self.assertContains(response, 'Регистрация')

	def test_subject_grade_wheels_show_scores_and_gpa_only_with_full_access(self):
		AcademicGrade.objects.create(profile=self.profile, subject='English', grade='5/5')
		AcademicGrade.objects.create(profile=self.profile, subject='Mathematics', grade='4/5')
		self.client.force_login(self.student)

		response = self.client.get(reverse('student-detail', args=[self.profile.pk]))

		self.assertContains(response, 'subject-grade-section')
		self.assertContains(response, 'title="English"')
		self.assertContains(response, 'title="Mathematics"')
		self.assertContains(response, '5/5')
		self.assertContains(response, '4/5')
		self.assertContains(response, '4.5/5')
		self.assertContains(response, reverse('student-profile'))

		self.client.logout()
		guest_response = self.client.get(
			reverse('student-detail', args=[self.profile.pk]),
			{'view': 'guest'},
		)
		self.assertNotContains(guest_response, 'subject-grade-section')
		self.assertNotContains(guest_response, 'title="English"')
		self.assertNotContains(guest_response, '4.5/5')

	def test_student_profile_editor_displays_existing_subject_grade_wheels(self):
		AcademicGrade.objects.create(profile=self.profile, subject='English', grade='4.1/5')
		self.client.force_login(self.student)

		response = self.client.get(reverse('student-profile'))

		self.assertContains(response, 'subject-grade-section')
		self.assertContains(response, '4.1/5')
		self.assertContains(response, 'GPA')
		self.assertContains(response, 'Добавить оценку')

	def test_guest_can_see_public_education_but_not_private_data(self):
		EducationEntry.objects.create(
			profile=self.profile,
			level='school',
			institution_name='Школа № 5',
			start_year=2016,
		)
		AcademicGrade.objects.create(profile=self.profile, subject='Закрытая математика', grade='5')
		TestScore.objects.create(profile=self.profile, test_type='Закрытый тест', score=99, date=date(2025, 5, 20))

		response = self.client.get(reverse('student-detail', args=[self.profile.pk]))

		self.assertContains(response, 'Школа № 5')
		self.assertNotContains(response, '2007')
		self.assertNotContains(response, 'private-student@example.com')
		self.assertNotContains(response, 'Закрытая математика')
		self.assertNotContains(response, 'Закрытый тест')

	def test_student_profile_shows_real_application_status(self):
		Application.objects.create(
			student=self.student,
			institution=self.institution,
			program=self.program,
			status='documents',
		)
		self.client.force_login(self.student)

		response = self.client.get(reverse('student-profile'))

		self.assertContains(response, 'Мои заявления')
		self.assertContains(response, 'Нужны документы')
		self.assertContains(response, reverse('application-dashboard'))

	def test_student_can_add_education_test_result_and_grade(self):
		self.client.force_login(self.student)
		profile_url = reverse('student-profile')

		education_response = self.client.post(profile_url, {
			'profile_action': 'education',
			'level': 'school',
			'institution_name': 'Школа № 12',
			'start_year': '2016',
			'end_year': '2025',
			'specialty': 'Физико-математический класс',
		})
		self.assertRedirects(education_response, profile_url)
		self.assertTrue(EducationEntry.objects.filter(profile=self.profile, institution_name='Школа № 12').exists())

		score_response = self.client.post(profile_url, {
			'profile_action': 'test_score',
			'test_type': 'ОРТ',
			'score': '195',
			'date': '2025-05-20',
		})
		self.assertRedirects(score_response, profile_url)
		self.assertTrue(TestScore.objects.filter(profile=self.profile, test_type='ОРТ', score=195).exists())

		grade_response = self.client.post(profile_url, {
			'profile_action': 'grade',
			'subject': 'Математика',
			'grade': '5',
		})
		self.assertRedirects(grade_response, profile_url)
		self.assertTrue(AcademicGrade.objects.filter(profile=self.profile, subject='Математика', grade='5').exists())
		profile_response = self.client.get(profile_url)
		self.assertContains(profile_response, 'subject-grade-section')
		self.assertContains(profile_response, 'Математика')
		self.assertContains(profile_response, '5/5')

	def test_friend_request_can_be_sent_and_accepted(self):
		friend = get_user_model().objects.create_user(
			username='friend-candidate',
			password='StrongPass123!',
			role='student',
			first_name='Саида',
			last_name='Турсунова',
		)
		friend_profile = StudentProfile.objects.create(user=friend, full_name=friend.get_full_name())
		self.client.force_login(self.student)

		response = self.client.post(reverse('manage-friend', args=[friend.pk]), {'action': 'request'})

		self.assertRedirects(response, reverse('student-detail', args=[friend_profile.pk]))
		request = StudentFriendship.objects.get(from_student=self.student, to_student=friend)
		self.assertEqual(request.status, 'pending')

		self.client.force_login(friend)
		response = self.client.post(reverse('manage-friend', args=[self.student.pk]), {'action': 'accept'})

		self.assertRedirects(response, reverse('student-detail', args=[self.profile.pk]))
		request.refresh_from_db()
		self.assertEqual(request.status, 'accepted')
		self.assertTrue(StudentFriendship.objects.filter(from_student=friend, to_student=self.student, status='accepted').exists())

	def test_repeated_accept_after_request_was_processed_does_not_return_404(self):
		friend = get_user_model().objects.create_user(username='already-accepted-friend', password='StrongPass123!', role='student')
		friend_profile = StudentProfile.objects.create(user=friend, full_name='Уже друг')
		StudentFriendship.objects.create(from_student=friend, to_student=self.student, status='accepted')
		StudentFriendship.objects.create(from_student=self.student, to_student=friend, status='accepted')
		self.client.force_login(self.student)

		response = self.client.post(reverse('manage-friend', args=[friend.pk]), {'action': 'accept'})

		self.assertRedirects(response, reverse('student-detail', args=[friend_profile.pk]), fetch_redirect_response=False)
		self.assertContains(self.client.get(reverse('student-detail', args=[friend_profile.pk])), 'Вы уже друзья.')

	def test_stale_accept_after_request_was_removed_redirects_with_message(self):
		friend = get_user_model().objects.create_user(username='removed-request-friend', password='StrongPass123!', role='student')
		friend_profile = StudentProfile.objects.create(user=friend, full_name='Друг без запроса')
		self.client.force_login(self.student)

		response = self.client.post(reverse('manage-friend', args=[friend.pk]), {'action': 'accept'})

		self.assertRedirects(response, reverse('student-detail', args=[friend_profile.pk]), fetch_redirect_response=False)
		self.assertContains(self.client.get(reverse('student-detail', args=[friend_profile.pk])), 'Запрос уже обработан или отменён.')

	def test_incoming_request_is_shown_when_both_users_sent_requests(self):
		friend = get_user_model().objects.create_user(username='mutual-request-friend', password='StrongPass123!', role='student')
		friend_profile = StudentProfile.objects.create(user=friend, full_name='Встречный запрос')
		StudentFriendship.objects.create(from_student=self.student, to_student=friend, status='pending')
		StudentFriendship.objects.create(from_student=friend, to_student=self.student, status='pending')
		self.client.force_login(self.student)

		response = self.client.get(reverse('student-detail', args=[friend_profile.pk]))

		self.assertContains(response, 'Принять запрос дружбы')

	def test_student_can_remove_friendship(self):
		friend = get_user_model().objects.create_user(username='existing-friend', password='StrongPass123!', role='student')
		friend_profile = StudentProfile.objects.create(user=friend, full_name='Саида Турсунова')
		StudentFriendship.objects.create(from_student=self.student, to_student=friend, status='accepted')
		StudentFriendship.objects.create(from_student=friend, to_student=self.student, status='accepted')
		self.client.force_login(self.student)

		response = self.client.post(reverse('manage-friend', args=[friend.pk]), {'action': 'remove'})

		self.assertRedirects(response, reverse('student-detail', args=[friend_profile.pk]))
		self.assertFalse(StudentFriendship.objects.filter(Q(from_student=self.student, to_student=friend) | Q(from_student=friend, to_student=self.student)).exists())

	def test_personal_profile_lists_friends_and_followed_institutions(self):
		friend = get_user_model().objects.create_user(username='listed-friend', password='StrongPass123!', role='student')
		friend_profile = StudentProfile.objects.create(user=friend, full_name='Досум Абдиев')
		StudentFriendship.objects.create(from_student=self.student, to_student=friend, status='accepted')
		InstitutionFollow.objects.create(student=self.student, institution=self.institution)
		self.client.force_login(self.student)

		response = self.client.get(reverse('student-profile'))

		self.assertContains(response, 'Друзья')
		self.assertContains(response, 'Досум Абдиев')
		self.assertContains(response, reverse('student-detail', args=[friend_profile.pk]))
		self.assertContains(response, 'Вузы в подписках')
		self.assertContains(response, 'Связанный вуз')
		self.assertContains(response, reverse('institution-detail', args=[self.institution.pk]))

	def test_friend_list_is_not_rendered_on_public_student_profile(self):
		friend = get_user_model().objects.create_user(username='private-friend', password='StrongPass123!', role='student')
		StudentProfile.objects.create(user=friend, full_name='Закрытый друг')
		StudentFriendship.objects.create(from_student=self.student, to_student=friend, status='accepted')

		response = self.client.get(reverse('student-detail', args=[self.profile.pk]))

		self.assertNotContains(response, 'Друзья')
		self.assertNotContains(response, 'Закрытый друг')

	def test_student_can_send_accept_and_remove_friend_request(self):
		friend = get_user_model().objects.create_user(
			username='friend-workflow',
			password='StrongPass123!',
			role='student',
			first_name='Саида',
			last_name='Турсунова',
		)
		friend_profile = StudentProfile.objects.create(user=friend, full_name=friend.get_full_name())
		self.client.force_login(self.student)

		response = self.client.post(reverse('manage-friend', args=[friend.pk]), {'action': 'request'})

		self.assertRedirects(response, reverse('student-detail', args=[friend_profile.pk]))
		outgoing = StudentFriendship.objects.get(from_student=self.student, to_student=friend)
		self.assertEqual(outgoing.status, 'pending')

		self.client.force_login(friend)
		response = self.client.post(reverse('manage-friend', args=[self.student.pk]), {'action': 'accept'})
		self.assertRedirects(response, reverse('student-detail', args=[self.profile.pk]))
		outgoing.refresh_from_db()
		self.assertEqual(outgoing.status, 'accepted')
		self.client.force_login(self.student)
		response = self.client.get(reverse('student-profile'))
		self.assertContains(response, 'Саида Турсунова')

		self.client.post(reverse('manage-friend', args=[friend.pk]), {'action': 'remove'})
		self.assertFalse(StudentFriendship.objects.filter(
			Q(from_student=self.student, to_student=friend)
			| Q(from_student=friend, to_student=self.student),
		).exists())

	def test_personal_profile_shows_both_relationship_lists(self):
		friend = get_user_model().objects.create_user(username='dashboard-friend', password='StrongPass123!', role='student')
		StudentProfile.objects.create(user=friend, full_name='Друз Абдиев')
		StudentFriendship.objects.create(from_student=self.student, to_student=friend, status='accepted')
		InstitutionFollow.objects.create(student=self.student, institution=self.institution)
		self.client.force_login(self.student)

		response = self.client.get(reverse('student-profile'))

		self.assertContains(response, 'Друзья')
		self.assertContains(response, 'Друз Абдиев')
		self.assertContains(response, 'Вузы в подписках')
		self.assertContains(response, 'Связанный вуз')
