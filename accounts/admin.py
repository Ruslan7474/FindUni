from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


admin.site.site_header = 'FindUni — панель управления'
admin.site.site_title = 'Администрирование FindUni'
admin.site.index_title = 'Управление платформой'
admin.site.site_url = '/'
admin.site.empty_value_display = '—'


class RoleFilter(admin.SimpleListFilter):
	title = 'Роль на платформе'
	parameter_name = 'role'

	def lookups(self, request, model_admin):
		return User.ROLE_CHOICES

	def queryset(self, request, queryset):
		if self.value():
			return queryset.filter(role=self.value())
		return queryset


@admin.register(User)
class FindUniUserAdmin(UserAdmin):
	list_display = ('login_label', 'email_label', 'full_name_label', 'role_label', 'is_staff', 'is_active')
	list_filter = (RoleFilter, 'is_staff', 'is_active', 'groups')
	search_fields = ('username', 'email', 'first_name', 'last_name')
	ordering = ('username',)
	fieldsets = (
		(None, {'fields': ('username', 'password')}),
		('Личные данные', {'fields': ('first_name', 'last_name', 'email', 'role')}),
		('Доступ и разрешения', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
		('Важные даты', {'fields': ('last_login_label', 'date_joined_label')}),
	)
	readonly_fields = ('last_login_label', 'date_joined_label')
	add_fieldsets = (
		(None, {'classes': ('wide',), 'fields': ('username', 'email', 'first_name', 'last_name', 'password1', 'password2', 'role')}),
	)

	field_labels = {
		'username': 'Логин',
		'email': 'Электронная почта',
		'first_name': 'Имя',
		'last_name': 'Фамилия',
		'role': 'Роль на платформе',
		'password': 'Пароль',
		'password1': 'Пароль',
		'password2': 'Подтверждение пароля',
		'is_active': 'Активен',
		'is_staff': 'Доступ в панель администрирования',
		'is_superuser': 'Полные права администратора',
		'groups': 'Группы доступа',
		'user_permissions': 'Индивидуальные разрешения',
		'last_login': 'Последний вход',
		'date_joined': 'Дата регистрации',
	}

	def get_form(self, request, obj=None, **kwargs):
		form = super().get_form(request, obj, **kwargs)
		for field_name, label in self.field_labels.items():
			if field_name in form.base_fields:
				form.base_fields[field_name].label = label
		if 'username' in form.base_fields:
			form.base_fields['username'].help_text = 'Обязательное поле. Не более 150 символов: буквы, цифры и символы @/./+/-/_.'
		if 'password1' in form.base_fields:
			form.base_fields['password1'].help_text = 'Пароль должен содержать не менее 8 символов, не быть распространённым или состоять только из цифр.'
		if 'password2' in form.base_fields:
			form.base_fields['password2'].help_text = 'Введите тот же пароль ещё раз для проверки.'
		return form

	@admin.display(description='Логин', ordering='username')
	def login_label(self, obj):
		return obj.username

	@admin.display(description='Электронная почта', ordering='email')
	def email_label(self, obj):
		return obj.email or '—'

	@admin.display(description='Имя и фамилия')
	def full_name_label(self, obj):
		return obj.get_full_name() or '—'

	@admin.display(description='Роль', ordering='role')
	def role_label(self, obj):
		return obj.get_role_display()

	@admin.display(description='Последний вход')
	def last_login_label(self, obj):
		return obj.last_login or '—'

	@admin.display(description='Дата регистрации')
	def date_joined_label(self, obj):
		return obj.date_joined
