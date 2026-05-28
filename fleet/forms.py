from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User, Group
from .models import Automobile, Driver, TravelLog


class AutomobileForm(forms.ModelForm):
    class Meta:
        model = Automobile
        fields = '__all__'
        widgets = {
            'inspection_due_date': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date', 'class': 'form-control'}),
            'insurance_due_date': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date', 'class': 'form-control'}),
            'make': forms.TextInput(attrs={'class': 'form-control'}),
            'model': forms.TextInput(attrs={'class': 'form-control'}),
            'license_plate': forms.TextInput(attrs={'class': 'form-control'}),
            'fuel_consumption_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'current_mileage': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class DriverForm(forms.ModelForm):
    class Meta:
        model = Driver
        fields = ['last_name', 'first_name', 'middle_name', 'contact_info']
        widgets = {
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'middle_name': forms.TextInput(attrs={'class': 'form-control'}),
            'contact_info': forms.TextInput(attrs={'class': 'form-control'}),
        }


class TravelLogForm(forms.ModelForm):
    class Meta:
        model = TravelLog
        fields = '__all__'
        widgets = {
            'start_date': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date', 'class': 'form-control'}),
            'departure_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'end_date': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date', 'class': 'form-control'}),
            'return_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'automobile': forms.Select(attrs={'class': 'form-select', 'id': 'id_automobile'}),
            'driver': forms.Select(attrs={'class': 'form-select'}),
            'log_number': forms.TextInput(attrs={'class': 'form-control'}),
            'start_mileage': forms.NumberInput(attrs={'class': 'form-control', 'id': 'id_start_mileage'}),
            'end_mileage': forms.NumberInput(attrs={'class': 'form-control'}),
            'route': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'fuel_balance_start': forms.NumberInput(attrs={'class': 'form-control'}),
            'fuel_issued': forms.NumberInput(attrs={'class': 'form-control'}),
            'fuel_balance_end': forms.NumberInput(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        start_mileage = cleaned_data.get('start_mileage')
        end_mileage = cleaned_data.get('end_mileage')

        if start_mileage is not None and end_mileage is not None:
            if end_mileage < start_mileage:
                self.add_error('end_mileage', "Конечный пробег не может быть меньше начального!")

        return cleaned_data


class UserRegistrationForm(forms.ModelForm):
    first_name = forms.CharField(label="Имя", widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(label="Фамилия", widget=forms.TextInput(attrs={'class': 'form-control'}))
    middle_name = forms.CharField(label="Отчество (необязательно)", required=False,
                                  widget=forms.TextInput(attrs={'class': 'form-control'}))
    phone_number = forms.CharField(label="Номер телефона", widget=forms.TextInput(attrs={'class': 'form-control'}))

    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}), label="Пароль")
    role = forms.ModelChoiceField(queryset=Group.objects.all(), label="Роль сотрудника",
                                  widget=forms.Select(attrs={'class': 'form-select'}))

    class Meta:
        model = User
        fields = ['username', 'email', 'last_name', 'first_name', 'password']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']

        if commit:
            user.save()
            selected_group = self.cleaned_data['role']
            user.groups.add(selected_group)

            user.profile.middle_name = self.cleaned_data['middle_name']
            user.profile.phone_number = self.cleaned_data['phone_number']
            user.profile.save()

        return user


class UserEditForm(forms.ModelForm):
    first_name = forms.CharField(label="Имя", widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(label="Фамилия", widget=forms.TextInput(attrs={'class': 'form-control'}))
    middle_name = forms.CharField(label="Отчество (необязательно)", required=False,
                                  widget=forms.TextInput(attrs={'class': 'form-control'}))
    phone_number = forms.CharField(label="Номер телефона", widget=forms.TextInput(attrs={'class': 'form-control'}))
    role = forms.ModelChoiceField(queryset=Group.objects.all(), label="Роль сотрудника",
                                  widget=forms.Select(attrs={'class': 'form-select'}))

    class Meta:
        model = User
        fields = ['username', 'email', 'last_name', 'first_name']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            if self.instance.groups.exists():
                self.fields['role'].initial = self.instance.groups.first()
            if hasattr(self.instance, 'profile'):
                self.fields['middle_name'].initial = self.instance.profile.middle_name
                self.fields['phone_number'].initial = self.instance.profile.phone_number

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()

            user.groups.clear()
            selected_group = self.cleaned_data['role']
            user.groups.add(selected_group)

            if not hasattr(user, 'profile'):
                from .models import UserProfile
                UserProfile.objects.create(user=user)

            user.profile.middle_name = self.cleaned_data['middle_name']
            user.profile.phone_number = self.cleaned_data['phone_number']
            user.profile.save()
        return user


class ReportFilterForm(forms.Form):
    date_from = forms.DateField(
        required=False,
        label="Дата С",
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    date_to = forms.DateField(
        required=False,
        label="Дата По",
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    automobile = forms.ModelChoiceField(
        queryset=Automobile.objects.all(),
        required=False,
        label="Автомобиль",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    driver = forms.ModelChoiceField(
        queryset=Driver.objects.all(),
        required=False,
        label="Водитель",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
