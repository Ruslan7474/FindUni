from django import forms
from .models import AcademicGrade, Comment, EducationEntry, StudentProfile, TestScore

class StudentProfileForm(forms.ModelForm):
    class Meta:
        model = StudentProfile
        fields = ('full_name', 'date_of_birth', 'city', 'nationality', 'citizenship', 'bio', 'interests', 'languages', 'avatar', 'email_visible', 'contacts_visible')
        labels = {
            'full_name': 'Имя и фамилия',
            'date_of_birth': 'Дата рождения',
            'city': 'Город',
            'nationality': 'Национальность',
            'citizenship': 'Гражданство',
            'bio': 'О себе',
            'interests': 'Интересующие направления',
            'languages': 'Языки',
            'avatar': 'Фото профиля',
            'email_visible': 'Показывать электронную почту учебным заведениям',
            'contacts_visible': 'Показывать контактные данные',
        }
        error_messages = {
            'full_name': {'required': 'Укажите имя и фамилию.'},
            'date_of_birth': {'invalid': 'Введите корректную дату.'},
            'avatar': {'invalid_image': 'Загрузите корректное изображение.'},
        }

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
        labels = {'text': 'Комментарий'}
        widgets = {
            'text': forms.Textarea(attrs={
                'rows': 1,
                'placeholder': 'Напишите что-нибудь...',
                'maxlength': 500,
            }),
        }

class EducationEntryForm(forms.ModelForm):
    class Meta:
        model = EducationEntry
        fields = ('level', 'institution_name', 'start_year', 'end_year', 'specialty')
        labels = {
            'level': 'Уровень образования',
            'institution_name': 'Учебное заведение',
            'start_year': 'Год начала',
            'end_year': 'Год окончания',
            'specialty': 'Направление или специальность',
        }
        error_messages = {
            'institution_name': {'required': 'Укажите учебное заведение.'},
            'start_year': {'required': 'Укажите год начала.'},
        }

class TestScoreForm(forms.ModelForm):
    class Meta:
        model = TestScore
        fields = ('test_type', 'score', 'date')
        labels = {
            'test_type': 'Название теста или экзамена',
            'score': 'Результат',
            'date': 'Дата сдачи',
        }


class AcademicGradeForm(forms.ModelForm):
    class Meta:
        model = AcademicGrade
        fields = ('subject', 'grade')
        labels = {
            'subject': 'Предмет',
            'grade': 'Оценка или средний балл',
        }
        error_messages = {
            'subject': {'required': 'Укажите предмет.'},
            'grade': {'required': 'Укажите оценку.'},
        }
