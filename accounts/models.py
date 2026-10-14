from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_CHOICES = [('student', 'Студент'), ('institution', 'Учебное заведение'), ('admin', 'Администратор')]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')

    class Meta(AbstractUser.Meta):
        verbose_name = 'пользователь'
        verbose_name_plural = 'пользователи'

    def __str__(self):
        return self.get_full_name() or self.email or self.username
