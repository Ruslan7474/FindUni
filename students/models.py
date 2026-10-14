from django.conf import settings
from django.core.validators import MaxLengthValidator
from django.db import models


class StudentProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='student_profile')
    full_name = models.CharField(max_length=150, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    city = models.CharField(max_length=100, blank=True)
    nationality = models.CharField(max_length=100, blank=True)
    citizenship = models.CharField(max_length=100, blank=True)
    bio = models.TextField(blank=True)
    interests = models.TextField(blank=True)
    languages = models.CharField(max_length=200, blank=True)
    avatar = models.ImageField(upload_to='avatars/students/', blank=True)
    email_visible = models.BooleanField(default=False)
    contacts_visible = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'профиль абитуриента'
        verbose_name_plural = 'профили абитуриентов'

    def __str__(self):
        return self.full_name or self.user.get_full_name() or self.user.username


class EducationEntry(models.Model):
    LEVEL_CHOICES = [('school', 'Школа'), ('college', 'Колледж'), ('university', 'Вуз')]
    profile = models.ForeignKey(StudentProfile, related_name='education', on_delete=models.CASCADE)
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES)
    institution_name = models.CharField(max_length=150)
    start_year = models.PositiveSmallIntegerField()
    end_year = models.PositiveSmallIntegerField(null=True, blank=True)
    specialty = models.CharField(max_length=150, blank=True)

    class Meta:
        verbose_name = 'запись об образовании'
        verbose_name_plural = 'образование абитуриентов'

    def __str__(self):
        return f'{self.institution_name} — {self.profile}'


class TestScore(models.Model):
    profile = models.ForeignKey(StudentProfile, related_name='test_scores', on_delete=models.CASCADE)
    test_type = models.CharField(max_length=50)
    score = models.PositiveSmallIntegerField()
    date = models.DateField()

    class Meta:
        verbose_name = 'результат экзамена'
        verbose_name_plural = 'результаты экзаменов'

    def __str__(self):
        return f'{self.test_type}: {self.score}'


class AcademicGrade(models.Model):
    profile = models.ForeignKey(StudentProfile, related_name='grades', on_delete=models.CASCADE)
    subject = models.CharField(max_length=100)
    grade = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('subject', 'pk')
        verbose_name = 'оценка по предмету'
        verbose_name_plural = 'оценки по предметам'

    def __str__(self):
        return f'{self.subject}: {self.grade}'


class StudentFriendship(models.Model):
    STATUS_CHOICES = [('pending', 'Ожидает ответа'), ('accepted', 'Друзья')]
    from_student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_friend_requests',
    )
    to_student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='received_friend_requests',
    )
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=('from_student', 'to_student'), name='unique_student_friend_request'),
            models.CheckConstraint(condition=~models.Q(from_student=models.F('to_student')), name='student_cannot_friend_self'),
        ]
        verbose_name = 'связь между абитуриентами'
        verbose_name_plural = 'дружба между абитуриентами'

    def __str__(self):
        return f'{self.from_student} → {self.to_student}: {self.get_status_display()}'


class InstitutionFollow(models.Model):
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='institution_follows',
    )
    institution = models.ForeignKey(
        'institutions.Institution',
        on_delete=models.CASCADE,
        related_name='student_follows',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-created_at',)
        constraints = [
            models.UniqueConstraint(fields=('student', 'institution'), name='unique_student_institution_follow'),
        ]
        verbose_name = 'подписка на учебное заведение'
        verbose_name_plural = 'подписки на учебные заведения'

    def __str__(self):
        return f'{self.student} → {self.institution}'


class Comment(models.Model):
    profile = models.ForeignKey(StudentProfile, related_name='comments', on_delete=models.CASCADE)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='comments')
    parent = models.ForeignKey('self', related_name='replies', on_delete=models.CASCADE, null=True, blank=True)
    text = models.TextField(validators=[MaxLengthValidator(500)])
    created_at = models.DateTimeField(auto_now_add=True)
    is_removed = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'комментарий к профилю'
        verbose_name_plural = 'комментарии к профилям'

    def __str__(self):
        return f'{self.author} → {self.profile}'


class CommentVote(models.Model):
    VALUE_CHOICES = [('like', 'Нравится'), ('dislike', 'Не нравится')]
    comment = models.ForeignKey(Comment, related_name='votes', on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='comment_votes', on_delete=models.CASCADE)
    value = models.CharField(max_length=8, choices=VALUE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=('comment', 'user'), name='unique_comment_vote_per_user')]
        verbose_name = 'реакция на комментарий'
        verbose_name_plural = 'реакции на комментарии'

    def __str__(self):
        return f'{self.user} → {self.comment}: {self.get_value_display()}'
