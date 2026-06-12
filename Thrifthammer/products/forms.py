"""Forms for the products app."""

from django import forms


ISSUE_TYPE_CHOICES = [
    ('wrong_price',         'Price is incorrect'),
    ('in_stock_wrong',      'Shows in stock but item is out of stock'),
    ('out_of_stock_wrong',  'Shows out of stock but item is available'),
    ('wrong_link',          'Retailer link goes to wrong product'),
    ('wrong_product',       'Wrong product or image'),
    ('other',               'Other issue'),
]


class IssueReportForm(forms.Form):
    """Form for users to report a data problem on a product page."""

    ISSUE_TYPE_CHOICES = ISSUE_TYPE_CHOICES  # expose for view label lookup

    issue_type = forms.ChoiceField(
        choices=ISSUE_TYPE_CHOICES,
        label='What is the problem?',
        widget=forms.Select(attrs={'class': 'form-control'}),
    )
    description = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 4,
            'class': 'form-control',
            'placeholder': 'Please describe the issue — e.g. the correct price, '
                           'the right link, or what is wrong with the current data.',
        }),
        max_length=1000,
        label='Details',
        help_text='Up to 1 000 characters.',
    )
    contact_email = forms.EmailField(
        required=False,
        label='Your email (optional)',
        max_length=254,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'you@example.com',
        }),
        help_text='Leave your email if you would like a reply.',
    )

    def clean_contact_email(self):
        email = self.cleaned_data.get('contact_email', '')
        if email and email.lower().endswith('@example.com'):
            raise forms.ValidationError('Please enter a valid email address.')
        return email
