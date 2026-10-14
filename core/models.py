from django.db import models


class City(models.Model):
    name = models.CharField(max_length=100)

    class Meta:
        verbose_name = 'город'
        verbose_name_plural = 'города'

    def __str__(self):
        return self.name


class TestType(models.Model):
    name = models.CharField(max_length=50)

    class Meta:
        verbose_name = 'тип экзамена'
        verbose_name_plural = 'типы экзаменов'

    def __str__(self):
        return self.name


class Direction(models.Model):
    name = models.CharField(max_length=150)

    class Meta:
        verbose_name = 'направление подготовки'
        verbose_name_plural = 'направления подготовки'

    def __str__(self):
        return self.name
