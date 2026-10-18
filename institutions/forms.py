from django import forms
from django.forms import inlineformset_factory
from django.utils.translation import get_language
from .models import Institution, Program, ProgramDocumentRequirement, InstitutionPhoto, Review

def _localize_fields(form, labels):
    index = {'en': 0, 'ky': 1}.get(get_language())
    if index is not None:
        for field_name, values in labels.items():
            form.fields[field_name].label = values[index]

class InstitutionForm(forms.ModelForm):
    class Meta:
        model = Institution
        fields = ('name', 'institution_type', 'city', 'address', 'description', 'history', 'website', 'phone', 'email', 'logo', 'logo_url')
        labels = {
            'name': 'Название учебного заведения',
            'institution_type': 'Тип учебного заведения',
            'city': 'Страна',
            'address': 'Адрес',
            'description': 'Описание',
            'history': 'История учебного заведения',
            'website': 'Сайт',
            'phone': 'Телефон',
            'email': 'Электронная почта для абитуриентов',
            'logo': 'Логотип',
            'logo_url': 'Ссылка на логотип',
        }
        error_messages = {
            'name': {'required': 'Укажите название учебного заведения.'},
            'institution_type': {'required': 'Выберите тип учебного заведения.'},
            'city': {'required': 'Укажите страну.'},
            'website': {'invalid': 'Введите корректный адрес сайта.'},
            'logo': {'invalid_image': 'Загрузите корректное изображение.'},
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _localize_fields(self, {
            'name': ('Institution name', 'Окуу жайдын аталышы'), 'institution_type': ('Institution type', 'Окуу жайдын түрү'),
            'city': ('Country', 'Өлкө'), 'address': ('Address details', 'Дарек тууралуу маалымат'), 'description': ('Description', 'Сүрөттөмө'),
            'history': ('Institution history', 'Окуу жайдын тарыхы'), 'website': ('Website', 'Сайт'),
            'phone': ('Phone', 'Телефон'), 'email': ('Contact email for applicants', 'Абитуриенттер үчүн электрондук почта'),
            'logo': ('Logo file', 'Логотип файлы'), 'logo_url': ('Logo URL', 'Логотиптин шилтемеси'),
        })
        self.fields['address'].help_text = {
            'en': 'Optional city, region or street address within the country.',
            'ky': 'Өлкөнүн ичиндеги шаарды, аймакты же көчө дарегин тактоо үчүн.',
        }.get(get_language(), 'Укажите город, регион или улицу внутри страны.')

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
            'price': 'Стоимость ($)',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _localize_fields(self, {
            'name': ('Program name', 'Программанын аталышы'), 'direction': ('Field of study', 'Даярдоо багыты'),
            'language': ('Language of instruction', 'Окутуу тили'), 'form': ('Study format', 'Окуу формасы'),
            'duration': ('Duration', 'Окуу мөөнөтү'), 'places': ('Number of places', 'Орундардын саны'),
            'grant_places': ('Grant-funded places', 'Гранттык орундар'), 'price': ('Tuition ($)', 'Окуу акысы ($)'),
        })


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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _localize_fields(self, {'name': ('Document name', 'Документтин аталышы'), 'file_format': ('Allowed file format', 'Уруксат берилген файл форматы'), 'is_required': ('Required document', 'Милдеттүү документ')})


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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _localize_fields(self, {'rating': ('Rating', 'Рейтинг'), 'text': ('Review', 'Пикир')})


class InstitutionPhotoForm(forms.ModelForm):
    class Meta:
        model = InstitutionPhoto
        fields = ('image', 'image_url')
        labels = {'image': 'Фотография учебного заведения', 'image_url': 'Ссылка на фотографию учебного заведения'}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _localize_fields(self, {
            'image': ('Photo file', 'Сүрөт файлы'),
            'image_url': ('Institution photo URL', 'Окуу жайдын сүрөтүнө шилтеме'),
        })

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data.get('DELETE') and not cleaned_data.get('image') and not cleaned_data.get('image_url') and self.has_changed():
            self.add_error('image_url', 'Укажите файл фотографии или ссылку на неё.')
        return cleaned_data


InstitutionPhotoFormSet = inlineformset_factory(
    Institution,
    InstitutionPhoto,
    form=InstitutionPhotoForm,
    extra=1,
    can_delete=True,
)
