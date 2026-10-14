from django.contrib import admin
from .models import Application
from core.admin import RussianFieldListFilter, RussianModelAdmin


class ApplicationStatusFilter(RussianFieldListFilter):
	title = 'Статус заявления'
	parameter_name = 'status'


@admin.register(Application)
class ApplicationAdmin(RussianModelAdmin):
	list_display = ('student_label', 'institution_label', 'program_label', 'status_label', 'created_label', 'updated_label')
	list_filter = (ApplicationStatusFilter,)
	search_fields = ('student__username', 'student__email', 'student__first_name', 'student__last_name', 'institution__name', 'program__name')
	readonly_fields = ('created_label', 'updated_label')
	date_hierarchy = 'created_at'
	field_labels = {
		'student': 'Абитуриент', 'institution': 'Учебное заведение', 'program': 'Программа',
		'message': 'Сопроводительное сообщение', 'status': 'Статус заявления', 'rejection_reason': 'Причина отказа',
	}

	@admin.display(description='Абитуриент', ordering='student__username')
	def student_label(self, obj):
		return obj.student.get_full_name() or obj.student.username

	@admin.display(description='Учебное заведение', ordering='institution__name')
	def institution_label(self, obj):
		return obj.institution.name

	@admin.display(description='Программа', ordering='program__name')
	def program_label(self, obj):
		return obj.program.name

	@admin.display(description='Статус', ordering='status')
	def status_label(self, obj):
		return obj.get_status_display()

	@admin.display(description='Дата отправки', ordering='created_at')
	def created_label(self, obj):
		return obj.created_at

	@admin.display(description='Последнее изменение', ordering='updated_at')
	def updated_label(self, obj):
		return obj.updated_at
