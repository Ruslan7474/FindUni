from django.contrib import admin
from django.db import models
from .models import City, Direction, TestType


class RussianModelAdmin(admin.ModelAdmin):
	field_labels = {}

	def formfield_for_dbfield(self, db_field, request, **kwargs):
		formfield = super().formfield_for_dbfield(db_field, request, **kwargs)
		if formfield and db_field.name in self.field_labels:
			formfield.label = self.field_labels[db_field.name]
		return formfield


class RussianFieldListFilter(admin.SimpleListFilter):
	def lookups(self, request, model_admin):
		field = model_admin.model._meta.get_field(self.parameter_name)
		if field.choices:
			return [(str(value), label) for value, label in field.flatchoices if value not in (None, '')]
		if isinstance(field, models.BooleanField):
			return [('1', 'Да'), ('0', 'Нет')]
		if field.is_relation:
			related_model = field.remote_field.model
			return [(str(value), label) for value, label in related_model.objects.values_list('pk', str(field.remote_field.field_name))[:100]]
		values = model_admin.get_queryset(request).order_by().values_list(self.parameter_name, flat=True).distinct()
		return [(str(value), str(value)) for value in values if value not in (None, '')][:50]

	def queryset(self, request, queryset):
		if self.value() is None:
			return queryset
		field = queryset.model._meta.get_field(self.parameter_name)
		value = self.value() == '1' if isinstance(field, models.BooleanField) else self.value()
		return queryset.filter(**{self.parameter_name: value})


@admin.register(City)
class CityAdmin(RussianModelAdmin):
	list_display = ('name_label',)
	search_fields = ('name',)
	field_labels = {'name': 'Название города'}

	@admin.display(description='Город', ordering='name')
	def name_label(self, obj):
		return obj.name


@admin.register(TestType)
class TestTypeAdmin(RussianModelAdmin):
	list_display = ('name_label',)
	search_fields = ('name',)
	field_labels = {'name': 'Название типа экзамена'}

	@admin.display(description='Тип экзамена', ordering='name')
	def name_label(self, obj):
		return obj.name


@admin.register(Direction)
class DirectionAdmin(RussianModelAdmin):
	list_display = ('name_label',)
	search_fields = ('name',)
	field_labels = {'name': 'Название направления'}

	@admin.display(description='Направление подготовки', ordering='name')
	def name_label(self, obj):
		return obj.name
