import uuid

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.core.exceptions import ValidationError
from django.db import transaction
from institutions.models import Institution
from students.models import StudentProfile

User = get_user_model()

class RegistrationForm(UserCreationForm):
    role = forms.ChoiceField(
        label='Кем вы будете на FindUni?',
        choices=(('student', 'Абитуриент'), ('institution', 'Учебное заведение')),
        initial='student',
        widget=forms.RadioSelect,
        error_messages={'required': 'Выберите тип аккаунта.'},
    )
    name = forms.CharField(
        label='Имя',
        max_length=150,
        error_messages={'required': 'Заполните это поле.'},
    )
    last_name = forms.CharField(
        label='Фамилия',
        max_length=150,
        required=False,
        error_messages={'required': 'Укажите фамилию.'},
    )
    email = forms.EmailField(
        label='Email',
        required=True,
        error_messages={
            'required': 'Укажите email.',
            'invalid': 'Введите корректный email.',
        },
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('email',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        selected_role = self.data.get('role') if self.is_bound else self.initial.get('role', 'student')
        self.fields['last_name'].required = selected_role != 'institution'
        if selected_role == 'institution':
            self.fields['name'].label = 'Название учебного заведения'
        self.fields['email'].label = 'Email'
        self.fields['password1'].label = 'Пароль'
        self.fields['password2'].label = 'Подтверждение пароля'
        self.fields['password1'].error_messages['required'] = 'Укажите пароль.'
        self.fields['password2'].error_messages['required'] = 'Подтвердите пароль.'
        self.fields['password1'].help_text = ''
        self.fields['password2'].help_text = ''
        self.order_fields(('role', 'name', 'last_name', 'email', 'password1', 'password2'))

    def clean_email(self):
        email = self.cleaned_data['email'].strip()
        if email and User.objects.filter(email__iexact=email).exists():
            raise ValidationError('Аккаунт с таким email уже существует.')
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = self.cleaned_data['role']
        user.username = f'finduni-{uuid.uuid4().hex}'
        user.first_name = self.cleaned_data['name'] if user.role == 'student' else ''
        user.last_name = self.cleaned_data.get('last_name', '') if user.role == 'student' else ''
        if commit:
            with transaction.atomic():
                user.save()
                if user.role == 'institution':
                    Institution.objects.create(
                        owner=user,
                        name=self.cleaned_data['name'],
                        email=user.email,
                    )
                elif user.role == 'student':
                    StudentProfile.objects.create(
                        user=user,
                        full_name=user.get_full_name(),
                    )
        return user


class EmailOrUsernameAuthenticationForm(AuthenticationForm):
    def clean(self):
        login = self.cleaned_data.get('username')
        if login and '@' in login:
            try:
                user = User.objects.get(email__iexact=login)
            except (User.DoesNotExist, User.MultipleObjectsReturned):
                pass
            else:
                self.cleaned_data['username'] = user.get_username()
        return super().clean()
