from decimal import Decimal

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import WatchlistItem


class RegistrationForm(UserCreationForm):
    """
    Extended registration form. Email is required — used for password reset.
    """
    email = forms.EmailField(required=True, help_text='Required for account recovery.')

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def save(self, commit=True):
        """Save user with email."""
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user


class WatchlistAlertForm(forms.ModelForm):
    """Configure the email alert for a single watchlist item."""

    class Meta:
        model = WatchlistItem
        fields = ('alert_type', 'target_price', 'alert_percent', 'email_alerts')
        widgets = {
            'alert_type': forms.Select(attrs={'class': 'alert-type-select'}),
            'target_price': forms.NumberInput(attrs={
                'step': '0.01', 'min': '0', 'placeholder': 'e.g. 29.99',
            }),
            'alert_percent': forms.NumberInput(attrs={
                'step': '1', 'min': '1', 'max': '99', 'placeholder': 'e.g. 15',
            }),
        }
        labels = {
            'alert_type': 'Alert me when',
            'target_price': 'Price threshold (£)',
            'alert_percent': '% off MSRP',
            'email_alerts': 'Send me an email when triggered',
        }

    def clean(self):
        cleaned = super().clean()
        alert_type = cleaned.get('alert_type')
        if alert_type == WatchlistItem.ALERT_PRICE and not cleaned.get('target_price'):
            raise forms.ValidationError('Please enter a target price.')
        if alert_type == WatchlistItem.ALERT_PCT_OFF:
            pct = cleaned.get('alert_percent')
            if not pct:
                raise forms.ValidationError('Please enter a percentage.')
            if not (Decimal('1') <= pct <= Decimal('99')):
                raise forms.ValidationError('Percentage must be between 1 and 99.')
        return cleaned


class ChangeEmailForm(forms.Form):
    """Change the account email address — requires current password for security."""
    new_email = forms.EmailField(label='New email address')
    current_password = forms.CharField(widget=forms.PasswordInput, label='Current password')

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_new_email(self):
        email = self.cleaned_data['new_email'].lower()
        if User.objects.filter(email__iexact=email).exclude(pk=self.user.pk).exists():
            raise forms.ValidationError('That email address is already in use.')
        return email

    def clean_current_password(self):
        pwd = self.cleaned_data['current_password']
        if not self.user.check_password(pwd):
            raise forms.ValidationError('Incorrect password.')
        return pwd


class ChangeUsernameForm(forms.Form):
    """Change the account username — requires current password for security."""
    new_username = forms.CharField(max_length=150, label='New username')
    current_password = forms.CharField(widget=forms.PasswordInput, label='Current password')

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_new_username(self):
        username = self.cleaned_data['new_username'].strip()
        if User.objects.filter(username__iexact=username).exclude(pk=self.user.pk).exists():
            raise forms.ValidationError('That username is already taken.')
        return username

    def clean_current_password(self):
        pwd = self.cleaned_data['current_password']
        if not self.user.check_password(pwd):
            raise forms.ValidationError('Incorrect password.')
        return pwd


class DeleteAccountForm(forms.Form):
    """Final confirmation step before permanently deleting an account."""
    password = forms.CharField(widget=forms.PasswordInput, label='Enter your password to confirm')

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_password(self):
        pwd = self.cleaned_data['password']
        if not self.user.check_password(pwd):
            raise forms.ValidationError('Incorrect password.')
        return pwd
