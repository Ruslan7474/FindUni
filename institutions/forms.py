from django import forms
from django.forms import inlineformset_factory
from .models import Institution, Program, ProgramDocumentRequirement, InstitutionPhoto, Review

class InstitutionForm(forms.ModelForm):
    class Meta:
        model = Institution
        fields = ('name', 'institution_type', 'city', 'address', 'description', 'history', 'website', 'phone', 'email', 'logo')
        labels = {
            'name': 'Название учебного заведения',
            'institution_type': 'Тип учебного заведения',
            'city': 'Город',
            'address': 'Адрес',
            'description': 'Описание',
            'history': 'История учебного заведения',
            'website': 'Сайт',
            'phone': 'Телефон',
            'email': 'Электронная почта для абитуриентов',
            'logo': 'Логотип',
        }
        error_messages = {
            'name': {'required': 'Укажите название учебного заведения.'},
            'institution_type': {'required': 'Выберите тип учебного заведения.'},
            'city': {'required': 'Укажите город.'},
            'website': {'invalid': 'Введите корректный адрес сайта.'},
            'logo': {'invalid_image': 'Загрузите корректное изображение.'},
        }

class ProgramForm(forms.ModelForm):
    class Meta:
        model = Program
        fields = ('name', 'direction', 'language', 'form', 'duration', 'places', 'grant_places', 'price')
        labels = {
            'name': 'Название программы',
            'direction': 'Направление подготовки',
            'language': 'Язык обучения',
            'form': 'Форма обучения',
            'duration': 'Срок обучения',
            'places': 'Количество мест',
            'grant_places': 'Грантовые места',
            'price': 'Стоимость',
        }


ProgramFormSet = inlineformset_factory(
    Institution,
    Program,
    form=ProgramForm,
    extra=1,
    can_delete=True,
)


class ProgramDocumentRequirementForm(forms.ModelForm):
    class Meta:
        model = ProgramDocumentRequirement
        fields = ('name', 'file_format', 'is_required')
        labels = {
            'name': 'Название документа',
            'file_format': 'Допустимый формат файла',
            'is_required': 'Обязательный документ',
        }


ProgramDocumentRequirementFormSet = inlineformset_factory(
    Program,
    ProgramDocumentRequirement,
    form=ProgramDocumentRequirementForm,
    extra=0,
    can_delete=True,
    max_num=100,
    validate_max=True,
)

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ('rating', 'text')


class InstitutionPhotoForm(forms.ModelForm):
    class Meta:
        model = InstitutionPhoto
        fields = ('image',)
        labels = {'image': 'Фотография учебного заведения'}


InstitutionPhotoFormSet = inlineformset_factory(
    Institution,
    InstitutionPhoto,
    form=InstitutionPhotoForm,
    extra=1,
    can_delete=True,
)
