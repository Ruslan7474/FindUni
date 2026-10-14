from django.contrib import admin
from .models import Institution, Program, ProgramDocumentRequirement, InstitutionPhoto, Review
from core.admin import RussianFieldListFilter, RussianModelAdmin


class InstitutionTypeFilter(RussianFieldListFilter):
	title = 'Тип заведения'
	parameter_name = 'institution_type'


class InstitutionApprovalFilter(RussianFieldListFilter):
	title = 'Статус модерации'
	parameter_name = 'approved'


class ProgramLanguageFilter(RussianFieldListFilter):
	title = 'Язык обучения'
	parameter_name = 'language'


class ReviewRatingFilter(RussianFieldListFilter):
	title = 'Оценка'
	parameter_name = 'rating'


class ReviewModerationFilter(RussianFieldListFilter):
	title = 'Статус модерации'
	parameter_name = 'is_removed'


@admin.register(Institution)
class InstitutionAdmin(RussianModelAdmin):
	list_display = ('name_label', 'type_label', 'city_label', 'approval_label', 'rating_label', 'rating_count_label')
	list_filter = (InstitutionTypeFilter, InstitutionApprovalFilter)
	search_fields = ('name', 'city', 'email', 'phone')
	list_per_page = 30
	exclude = ('rating', 'rating_count')
	field_labels = {
		'owner': 'Аккаунт владельца', 'name': 'Название', 'institution_type': 'Тип заведения',
		'city': 'Город', 'address': 'Адрес', 'description': 'Описание', 'history': 'История',
		'website': 'Сайт', 'phone': 'Телефон', 'email': 'Электронная почта', 'logo': 'Логотип',
		'approved': 'Одобрено модератором',
	}
	readonly_fields = ('rating_label', 'rating_count_label', 'created_label')

	@admin.display(description='Название', ordering='name')
	def name_label(self, obj):
		return obj.name

	@admin.display(description='Тип заведения', ordering='institution_type')
	def type_label(self, obj):
		return obj.get_institution_type_display()

	@admin.display(description='Город', ordering='city')
	def city_label(self, obj):
		return obj.city

	@admin.display(description='Одобрено', boolean=True, ordering='approved')
	def approval_label(self, obj):
		return obj.approved

	@admin.display(description='Рейтинг')
	def rating_label(self, obj):
		return f'{obj.rating:.1f}' if obj.rating_count else '—'

	@admin.display(description='Количество оценок', ordering='rating_count')
	def rating_count_label(self, obj):
		return obj.rating_count

	@admin.display(description='Дата добавления')
	def created_label(self, obj):
		return obj.created_at


@admin.register(Program)
class ProgramAdmin(RussianModelAdmin):
	list_display = ('name_label', 'institution_label', 'language_label', 'duration_label', 'places_label', 'grant_places_label', 'price_label')
	list_filter = (ProgramLanguageFilter,)
	search_fields = ('name', 'institution__name', 'language')
	field_labels = {
		'institution': 'Учебное заведение', 'name': 'Название программы', 'direction': 'Направление подготовки', 'language': 'Язык обучения',
		'form': 'Форма обучения', 'duration': 'Срок обучения', 'places': 'Количество мест',
		'grant_places': 'Грантовые места', 'price': 'Стоимость',
	}

	@admin.display(description='Программа', ordering='name')
	def name_label(self, obj):
		return obj.name

	@admin.display(description='Учебное заведение', ordering='institution__name')
	def institution_label(self, obj):
		return obj.institution.name

	@admin.display(description='Язык')
	def language_label(self, obj):
		return obj.language or '—'

	@admin.display(description='Срок обучения')
	def duration_label(self, obj):
		return obj.duration or '—'

	@admin.display(description='Количество мест', ordering='places')
	def places_label(self, obj):
		return obj.places

	@admin.display(description='Грантовые места', ordering='grant_places')
	def grant_places_label(self, obj):
		return obj.grant_places

	@admin.display(description='Стоимость', ordering='price')
	def price_label(self, obj):
		return obj.price


@admin.register(ProgramDocumentRequirement)
class ProgramDocumentRequirementAdmin(RussianModelAdmin):
	list_display = ('name', 'program', 'format_label', 'required_label')
	list_filter = ('file_format', 'is_required')
	search_fields = ('name', 'program__name', 'program__institution__name')
	field_labels = {
		'program': 'Программа', 'name': 'Название документа',
		'file_format': 'Формат файла', 'is_required': 'Обязательный документ',
	}

	@admin.display(description='Формат файла')
	def format_label(self, obj):
		return obj.get_file_format_display()

	@admin.display(description='Обязательный документ', boolean=True)
	def required_label(self, obj):
		return obj.is_required
@admin.register(InstitutionPhoto)
class InstitutionPhotoAdmin(RussianModelAdmin):
	list_display = ('institution_label', 'image_label', 'created_label')
	search_fields = ('institution__name',)
	readonly_fields = ('created_label',)
	field_labels = {'institution': 'Учебное заведение', 'image': 'Фотография'}

	@admin.display(description='Учебное заведение', ordering='institution__name')
	def institution_label(self, obj):
		return obj.institution.name

	@admin.display(description='Файл')
	def image_label(self, obj):
		return obj.image.name

	@admin.display(description='Дата загрузки')
	def created_label(self, obj):
		return obj.created_at


@admin.register(Review)
class ReviewAdmin(RussianModelAdmin):
	list_display = ('institution_label', 'author_label', 'rating_label', 'removed_label', 'created_label')
	list_filter = (ReviewRatingFilter, ReviewModerationFilter)
	search_fields = ('institution__name', 'author__username', 'author__email', 'text')
	readonly_fields = ('created_label',)
	field_labels = {
		'institution': 'Учебное заведение', 'author': 'Автор', 'rating': 'Оценка',
		'text': 'Текст отзыва', 'is_removed': 'Скрыт модератором',
	}

	@admin.display(description='Учебное заведение', ordering='institution__name')
	def institution_label(self, obj):
		return obj.institution.name

	@admin.display(description='Автор', ordering='author__username')
	def author_label(self, obj):
		return obj.author.get_full_name() or obj.author.username

	@admin.display(description='Оценка', ordering='rating')
	def rating_label(self, obj):
		return f'{obj.rating}/5'

	@admin.display(description='Скрыт модератором', boolean=True, ordering='is_removed')
	def removed_label(self, obj):
		return obj.is_removed

	@admin.display(description='Дата создания', ordering='created_at')
	def created_label(self, obj):
		return obj.created_at
