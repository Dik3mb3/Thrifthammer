from django import forms

from .models import CollectionItem


class CollectionItemForm(forms.ModelForm):
    class Meta:
        model = CollectionItem
        fields = ('status', 'quantity', 'price_paid', 'notes')
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3}),
        }
