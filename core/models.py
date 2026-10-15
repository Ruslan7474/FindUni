from django.db import models
from django.conf import settings
from django.utils import timezone


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


class Announcement(models.Model):
    AUDIENCE_CHOICES = [
        ('all', 'Все абитуриенты и учебные заведения'),
        ('student', 'Только абитуриенты'),
        ('institution', 'Только учебные заведения'),
    ]
    title = models.CharField(max_length=180, verbose_name='Тема')
    body = models.TextField(verbose_name='Текст сообщения')
    audience = models.CharField(max_length=20, choices=AUDIENCE_CHOICES, default='all', verbose_name='Получатели')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата отправки')

    class Meta:
        ordering = ('-created_at',)
        verbose_name = 'объявление для почты'
        verbose_name_plural = 'объявления для почты'

    def __str__(self):
        return self.title


class Notification(models.Model):
    KIND_CHOICES = [
        ('announcement', 'Объявление'),
        ('comment', 'Комментарий'),
        ('application', 'Новое заявление'),
        ('application_status', 'Статус заявления'),
        ('friend_request', 'Запрос дружбы'),
        ('institution_follow', 'Новая подписка'),
    ]
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='inbox_notifications',
        verbose_name='Получатель',
    )
    kind = models.CharField(max_length=24, choices=KIND_CHOICES, verbose_name='Тип сообщения')
    title = models.CharField(max_length=180, verbose_name='Тема')
    body = models.TextField(verbose_name='Текст сообщения')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата получения')
    is_read = models.BooleanField(default=False, verbose_name='Прочитано')
    announcement = models.ForeignKey(
        Announcement,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='notifications',
        verbose_name='Объявление',
    )
    comment = models.ForeignKey(
        'students.Comment',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='notifications',
        verbose_name='Комментарий',
    )
    application = models.ForeignKey(
        'applications.Application',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='notifications',
        verbose_name='Заявление',
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='sent_inbox_notifications',
        verbose_name='Отправитель',
    )
    friendship = models.ForeignKey(
        'students.StudentFriendship',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name='Запрос дружбы',
    )
    follow = models.ForeignKey(
        'students.InstitutionFollow',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name='Подписка',
    )

    class Meta:
        ordering = ('-created_at', '-pk')
        verbose_name = 'сообщение в почте'
        verbose_name_plural = 'сообщения в почте'

    def __str__(self):
        return f'{self.user}: {self.title}'

    def mark_read(self):
        if not self.is_read:
            self.is_read = True
            self.save(update_fields=('is_read',))
