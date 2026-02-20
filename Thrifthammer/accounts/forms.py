from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import SecurityProfile


class RegistrationForm(UserCreationForm):
    """
    Extended registration form that adds email and a security question/answer
    for self-service password reset without needing an email backend.
    """
    email = forms.EmailField(required=True, help_text='Required. Used for account identification.')
    security_question = forms.ChoiceField(
        choices=SecurityProfile.QUESTIONS,
        help_text='Choose a security question for account recovery.',
    )
    security_answer = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={'autocomplete': 'off'}),
        help_text='Your answer is stored securely and is case-insensitive.',
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2', 'security_question', 'security_answer')

    def save(self, commit=True):
        """Save user and security profile atomically."""
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            SecurityProfile.objects.update_or_create(
                user=user,
                defaults={
                    'question': self.cleaned_data['security_question'],
                    'answer_hash': SecurityProfile.hash_answer(self.cleaned_data['security_answer']),
                },
            )
        return user


class ForgotPasswordStep1Form(forms.Form):
    """Step 1: look up the account by username and show the security question."""
    username = forms.CharField(max_length=150)


class ForgotPasswordStep2Form(forms.Form):
    """Step 2: verify security answer and set a new password."""
    security_answer = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={'autocomplete': 'off'}),
        label='Security Answer',
    )
    new_password1 = forms.CharField(
        widget=forms.PasswordInput,
        label='New Password',
        min_length=8,
    )
    new_password2 = forms.CharField(
        widget=forms.PasswordInput,
        label='Confirm New Password',
        min_length=8,
    )

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get('new_password1')
        p2 = cleaned.get('new_password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError('The two passwords do not match.')
        return cleaned
