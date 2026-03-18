"""Forms for the ThriftHammer blog app."""

from django import forms

from .models import Comment


class CommentForm(forms.ModelForm):
    """
    Simple form for posting a comment on a blog post.

    Only the body field is exposed — author and post are set in the view.
    """

    class Meta:
        model = Comment
        fields = ['body']
        widgets = {
            'body': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Share your thoughts…',
                'class': 'comment-textarea',
            }),
        }
        labels = {'body': ''}
