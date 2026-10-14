from django.contrib import admin
from core.admin import RussianFieldListFilter, RussianModelAdmin
from .models import AcademicGrade, Comment, CommentVote, EducationEntry, InstitutionFollow, StudentFriendship, StudentProfile, TestScore


class StudentCityFilter(RussianFieldListFilter):
	title = 'Город'
	parameter_name = 'city'


class StudentNationalityFilter(RussianFieldListFilter):
	title = 'Национальность'
	parameter_name = 'nationality'


class StudentCitizenshipFilter(RussianFieldListFilter):
	title = 'Гражданство'
	parameter_name = 'citizenship'


class StudentEducationLevelFilter(RussianFieldListFilter):
	title = 'Уровень образования'
	parameter_name = 'level'


class StudentTestTypeFilter(RussianFieldListFilter):
	title = 'Экзамен или тест'
	parameter_name = 'test_type'


class StudentGradeSubjectFilter(RussianFieldListFilter):
	title = 'Предмет'
	parameter_name = 'subject'


class FriendshipStatusFilter(RussianFieldListFilter):
	title = 'Статус связи'
	parameter_name = 'status'


class CommentModerationFilter(RussianFieldListFilter):
	title = 'Скрыт модератором'
	parameter_name = 'is_removed'


@admin.register(StudentProfile)
class StudentProfileAdmin(RussianModelAdmin):
	list_display = ('student_name', 'email_label', 'city_label', 'nationality_label', 'citizenship_label')
	list_filter = (StudentCityFilter, StudentNationalityFilter, StudentCitizenshipFilter)
	search_fields = ('full_name', 'user__first_name', 'user__last_name', 'user__email', 'city')
	readonly_fields = ('created_label', 'updated_label')
	field_labels = {
		'user': 'Аккаунт абитуриента', 'full_name': 'Имя и фамилия', 'date_of_birth': 'Дата рождения',
		'city': 'Город', 'nationality': 'Национальность', 'citizenship': 'Гражданство',
		'bio': 'О себе', 'interests': 'Интересующие направления', 'languages': 'Языки',
		'avatar': 'Фото профиля', 'email_visible': 'Показывать электронную почту',
		'contacts_visible': 'Показывать контакты',
	}

	@admin.display(description='Абитуриент', ordering='full_name')
	def student_name(self, obj):
		return obj.full_name or obj.user.get_full_name() or obj.user.username

	@admin.display(description='Электронная почта', ordering='user__email')
	def email_label(self, obj):
		return obj.user.email or '—'

	@admin.display(description='Город', ordering='city')
	def city_label(self, obj):
		return obj.city or '—'

	@admin.display(description='Национальность', ordering='nationality')
	def nationality_label(self, obj):
		return obj.nationality or '—'

	@admin.display(description='Гражданство', ordering='citizenship')
	def citizenship_label(self, obj):
		return obj.citizenship or '—'

	@admin.display(description='Последнее изменение', ordering='updated_at')
	def updated_label(self, obj):
		return obj.updated_at

	@admin.display(description='Дата создания')
	def created_label(self, obj):
		return obj.created_at


@admin.register(EducationEntry)
class EducationEntryAdmin(RussianModelAdmin):
	list_display = ('student_label', 'level_label', 'institution_label', 'start_year_label', 'end_year_label', 'specialty_label')
	list_filter = (StudentEducationLevelFilter,)
	search_fields = ('profile__full_name', 'profile__user__email', 'institution_name', 'specialty')
	field_labels = {
		'profile': 'Профиль абитуриента', 'level': 'Уровень образования', 'institution_name': 'Учебное заведение',
		'start_year': 'Год начала', 'end_year': 'Год окончания', 'specialty': 'Направление или специальность',
	}

	@admin.display(description='Абитуриент', ordering='profile__full_name')
	def student_label(self, obj):
		return obj.profile.full_name or obj.profile.user.get_full_name() or obj.profile.user.username

	@admin.display(description='Уровень', ordering='level')
	def level_label(self, obj):
		return obj.get_level_display()

	@admin.display(description='Учебное заведение', ordering='institution_name')
	def institution_label(self, obj):
		return obj.institution_name

	@admin.display(description='Направление')
	def specialty_label(self, obj):
		return obj.specialty or '—'

	@admin.display(description='Год начала', ordering='start_year')
	def start_year_label(self, obj):
		return obj.start_year

	@admin.display(description='Год окончания', ordering='end_year')
	def end_year_label(self, obj):
		return obj.end_year or '—'


@admin.register(TestScore)
class TestScoreAdmin(RussianModelAdmin):
	list_display = ('student_label', 'test_type_label', 'score_label', 'date_label')
	list_filter = (StudentTestTypeFilter,)
	search_fields = ('profile__full_name', 'profile__user__email', 'test_type')
	field_labels = {'profile': 'Профиль абитуриента', 'test_type': 'Экзамен или тест', 'score': 'Результат', 'date': 'Дата сдачи'}

	@admin.display(description='Абитуриент', ordering='profile__full_name')
	def student_label(self, obj):
		return obj.profile.full_name or obj.profile.user.get_full_name() or obj.profile.user.username

	@admin.display(description='Экзамен или тест', ordering='test_type')
	def test_type_label(self, obj):
		return obj.test_type

	@admin.display(description='Результат', ordering='score')
	def score_label(self, obj):
		return obj.score

	@admin.display(description='Дата сдачи', ordering='date')
	def date_label(self, obj):
		return obj.date


@admin.register(AcademicGrade)
class AcademicGradeAdmin(RussianModelAdmin):
	list_display = ('student_label', 'subject_label', 'grade_label', 'created_label')
	list_filter = (StudentGradeSubjectFilter,)
	search_fields = ('profile__full_name', 'profile__user__email', 'subject', 'grade')
	readonly_fields = ('created_label',)
	field_labels = {'profile': 'Профиль абитуриента', 'subject': 'Предмет', 'grade': 'Оценка'}

	@admin.display(description='Абитуриент', ordering='profile__full_name')
	def student_label(self, obj):
		return obj.profile.full_name or obj.profile.user.get_full_name() or obj.profile.user.username

	@admin.display(description='Предмет', ordering='subject')
	def subject_label(self, obj):
		return obj.subject

	@admin.display(description='Оценка', ordering='grade')
	def grade_label(self, obj):
		return obj.grade

	@admin.display(description='Дата добавления', ordering='created_at')
	def created_label(self, obj):
		return obj.created_at


@admin.register(StudentFriendship)
class StudentFriendshipAdmin(RussianModelAdmin):
	list_display = ('from_student_label', 'to_student_label', 'status_label', 'created_label')
	list_filter = (FriendshipStatusFilter,)
	search_fields = ('from_student__email', 'from_student__username', 'to_student__email', 'to_student__username')
	readonly_fields = ('created_label',)
	field_labels = {
		'from_student': 'Кто отправил запрос', 'to_student': 'Кому отправлен запрос',
		'status': 'Статус связи',
	}

	@admin.display(description='Отправитель', ordering='from_student__username')
	def from_student_label(self, obj):
		return obj.from_student.get_full_name() or obj.from_student.username

	@admin.display(description='Получатель', ordering='to_student__username')
	def to_student_label(self, obj):
		return obj.to_student.get_full_name() or obj.to_student.username

	@admin.display(description='Статус', ordering='status')
	def status_label(self, obj):
		return obj.get_status_display()

	@admin.display(description='Дата запроса', ordering='created_at')
	def created_label(self, obj):
		return obj.created_at


@admin.register(InstitutionFollow)
class InstitutionFollowAdmin(RussianModelAdmin):
	list_display = ('student_label', 'institution_label', 'created_label')
	search_fields = ('student__email', 'student__username', 'institution__name')
	readonly_fields = ('created_label',)
	field_labels = {'student': 'Абитуриент', 'institution': 'Учебное заведение'}

	@admin.display(description='Абитуриент', ordering='student__username')
	def student_label(self, obj):
		return obj.student.get_full_name() or obj.student.username

	@admin.display(description='Учебное заведение', ordering='institution__name')
	def institution_label(self, obj):
		return obj.institution.name

	@admin.display(description='Дата подписки', ordering='created_at')
	def created_label(self, obj):
		return obj.created_at


@admin.register(Comment)
class CommentAdmin(RussianModelAdmin):
	list_display = ('student_label', 'author_label', 'created_label', 'removed_label')
	list_filter = (CommentModerationFilter,)
	search_fields = ('profile__full_name', 'author__username', 'author__email', 'text')
	readonly_fields = ('created_label',)
	field_labels = {'profile': 'Профиль абитуриента', 'author': 'Автор', 'text': 'Текст комментария', 'is_removed': 'Скрыт модератором'}

	@admin.display(description='Абитуриент', ordering='profile__full_name')
	def student_label(self, obj):
		return obj.profile.full_name or obj.profile.user.username

	@admin.display(description='Автор', ordering='author__username')
	def author_label(self, obj):
		return obj.author.get_full_name() or obj.author.username

	@admin.display(description='Дата публикации', ordering='created_at')
	def created_label(self, obj):
		return obj.created_at

	@admin.display(description='Скрыт модератором', boolean=True, ordering='is_removed')
	def removed_label(self, obj):
		return obj.is_removed


@admin.register(CommentVote)
class CommentVoteAdmin(RussianModelAdmin):
	list_display = ('comment_label', 'user_label', 'value_label', 'created_at')
	list_filter = ('value',)
	search_fields = ('comment__text', 'user__username', 'user__email')
	field_labels = {'comment': 'Комментарий', 'user': 'Пользователь', 'value': 'Реакция'}

	@admin.display(description='Комментарий')
	def comment_label(self, obj):
		return obj.comment.text[:80]

	@admin.display(description='Пользователь')
	def user_label(self, obj):
		return obj.user.get_full_name() or obj.user.username

	@admin.display(description='Реакция')
	def value_label(self, obj):
		return obj.get_value_display()
