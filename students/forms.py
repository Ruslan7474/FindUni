from django import forms
from django.utils.translation import get_language
from .models import AcademicGrade, Comment, EducationEntry, StudentProfile, TestScore

def _localize_fields(form, labels):
    language = get_language()
    index = {'en': 0, 'ky': 1}.get(language)
    if index is not None:
        for field_name, values in labels.items():
            form.fields[field_name].label = values[index]

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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _localize_fields(self, {
            'full_name': ('Full name', 'Аты-жөнү'), 'date_of_birth': ('Date of birth', 'Туулган күнү'),
            'city': ('City', 'Шаар'), 'nationality': ('Nationality', 'Улуту'),
            'citizenship': ('Citizenship', 'Жарандыгы'), 'bio': ('About me', 'Өзүм жөнүндө'),
            'interests': ('Fields of interest', 'Кызыккан багыттары'), 'languages': ('Languages', 'Тилдери'),
            'avatar': ('Profile photo', 'Профилдин сүрөтү'), 'email_visible': ('Show email to institutions', 'Электрондук почтаны окуу жайларга көрсөтүү'),
            'contacts_visible': ('Show contact details', 'Байланыш маалыматын көрсөтүү'),
        })

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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _localize_fields(self, {'text': ('Comment', 'Комментарий')})
        if get_language() == 'en':
            self.fields['text'].widget.attrs['placeholder'] = 'Write something...'
        elif get_language() == 'ky':
            self.fields['text'].widget.attrs['placeholder'] = 'Бир нерсе жазыңыз...'

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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _localize_fields(self, {
            'level': ('Education level', 'Билим деңгээли'), 'institution_name': ('Institution', 'Окуу жай'),
            'start_year': ('Start year', 'Башталган жылы'), 'end_year': ('End year', 'Бүткөн жылы'),
            'specialty': ('Field or specialty', 'Багыты же адистиги'),
        })

class TestScoreForm(forms.ModelForm):
    class Meta:
        model = TestScore
        fields = ('test_type', 'score', 'date')
        labels = {
            'test_type': 'Название теста или экзамена',
            'score': 'Результат',
            'date': 'Дата сдачи',
        }
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _localize_fields(self, {'test_type': ('Test or exam name', 'Тесттин же экзамендин аталышы'), 'score': ('Score', 'Жыйынтык'), 'date': ('Date taken', 'Тапшырган күнү')})


class AcademicGradeForm(forms.ModelForm):
    grade = forms.DecimalField(
        min_value=0,
        max_value=5,
        max_digits=3,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'min': '0', 'max': '5', 'step': '0.1'}),
        help_text='Введите значение от 0 до 5.',
        error_messages={
            'max_value': 'Оценка или GPA не может превышать 5.',
            'min_value': 'Оценка не может быть меньше 0.',
        },
    )

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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _localize_fields(self, {'subject': ('Subject', 'Сабак'), 'grade': ('Grade or GPA', 'Баасы же орточо баллы')})
        language = get_language()
        if language == 'en':
            self.fields['grade'].help_text = 'Enter a value from 0 to 5.'
            self.fields['grade'].error_messages.update({
                'max_value': 'Grade or GPA cannot exceed 5.',
                'min_value': 'Grade cannot be less than 0.',
            })
        elif language == 'ky':
            self.fields['grade'].help_text = '0дөн 5ке чейинки маанини киргизиңиз.'
            self.fields['grade'].error_messages.update({
                'max_value': 'Баанын же GPAнын мааниси 5тен ашпашы керек.',
                'min_value': 'Баанын мааниси 0дөн төмөн болбошу керек.',
            })
