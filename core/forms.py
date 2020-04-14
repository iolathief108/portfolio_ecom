from django.contrib.auth.forms import UserCreationForm
from django import forms
from django.contrib.auth.models import User

from .models import User2, Product, Category, Country


class AccountRegistrationForm(UserCreationForm):
    email = forms.EmailField()
    first_name = forms.CharField(max_length=30)
    last_name = forms.CharField(max_length=30)

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email', 'password1', 'password2']


class UserRegistrationForm(forms.ModelForm):
    class Meta:
        model = User2
        fields = []


class NewProductForm(forms.ModelForm):
    category = forms.ModelChoiceField(queryset=Category.objects.all())
    country = forms.ModelChoiceField(queryset=Country.objects.all())

    class Meta:
        model = Product
        fields = ['name', 'brand', 'daily_cost', 'deposit_amount', 'description', 'category', 'country']


class AccountUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username']


class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User2
        fields = ['description', 'profile_pic']


