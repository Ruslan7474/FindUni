from django.conf import settings
from django.core.validators import MaxLengthValidator, MinValueValidator, MaxValueValidator
from django.db import models
from django.db.models import Avg, Count
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver


class Institution(models.Model):
    TYPE_CHOICES = [('college9', 'Колледж после 9 класса'), ('college11', 'Колледж-вуз после 11 класса'), ('university', 'Университет')]
    owner = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='institution_profile')
    name = models.CharField(max_length=160)
    institution_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    city = models.CharField(max_length=100)
    address = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    history = models.TextField(blank=True)
    website = models.URLField(blank=True)
    phone = models.CharField(max_length=40, blank=True)
    email = models.EmailField(blank=True)
    logo = models.ImageField(upload_to='logos/', blank=True)
    logo_url = models.URLField(blank=True)
    approved = models.BooleanField(default=False)
    rating = models.FloatField(default=0)
    rating_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'учебное заведение'
        verbose_name_plural = 'учебные заведения'

    def __str__(self):
        return self.name


class Program(models.Model):
    institution = models.ForeignKey(Institution, related_name='programs', on_delete=models.CASCADE)
    name = models.CharField(max_length=150)
    direction = models.CharField(max_length=150, blank=True)
    language = models.CharField(max_length=50, blank=True)
    form = models.CharField(max_length=50, blank=True)
    duration = models.CharField(max_length=50, blank=True)
    places = models.PositiveIntegerField(default=0)
    grant_places = models.PositiveIntegerField(default=0)
    price = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        verbose_name = 'образовательная программа'
        verbose_name_plural = 'образовательные программы'

    def __str__(self):
        return self.name


class ProgramDocumentRequirement(models.Model):
    FORMAT_CHOICES = [('jpg', 'JPG'), ('png', 'PNG'), ('pdf', 'PDF')]
    program = models.ForeignKey(Program, related_name='document_requirements', on_delete=models.CASCADE)
    name = models.CharField(max_length=150)
    file_format = models.CharField(max_length=8, choices=FORMAT_CHOICES)
    is_required = models.BooleanField(default=True)

    class Meta:
        ordering = ('pk',)
        verbose_name = 'требование к документу программы'
        verbose_name_plural = 'требования к документам программы'

    def __str__(self):
        return f'{self.program.name}: {self.name} ({self.get_file_format_display()})'


class InstitutionPhoto(models.Model):
    institution = models.ForeignKey(Institution, related_name='photos', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='institution-photos/', blank=True)
    image_url = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'фотография учебного заведения'
        verbose_name_plural = 'фотографии учебных заведений'

    def __str__(self):
        return f'{self.institution.name} — {self.image.name}'


class Review(models.Model):
    institution = models.ForeignKey(Institution, related_name='reviews', on_delete=models.CASCADE)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    text = models.TextField(validators=[MaxLengthValidator(2000)])
    created_at = models.DateTimeField(auto_now_add=True)
    is_removed = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'отзыв'
        verbose_name_plural = 'отзывы'

    def __str__(self):
        return f'{self.institution.name} — {self.rating}/5'


def refresh_institution_rating(institution_id):
    ratings = Review.objects.filter(institution_id=institution_id, is_removed=False).aggregate(
        average=Avg('rating'),
        count=Count('id'),
    )
    Institution.objects.filter(pk=institution_id).update(
        rating=ratings['average'] or 0,
        rating_count=ratings['count'],
    )


@receiver(post_save, sender=Review)
@receiver(post_delete, sender=Review)
def update_institution_rating(sender, instance, **kwargs):
    refresh_institution_rating(instance.institution_id)
