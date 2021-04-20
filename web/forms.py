from django import forms
from django import forms
from .models import Comment, Document


class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ('document', 'description')


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('comment', 'classification')
