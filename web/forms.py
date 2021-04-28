from django import forms
from django.forms import inlineformset_factory, BaseInlineFormSet
from .models import Comment, Document, Filter, FilterItem


class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ('document', 'description')


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('comment', 'classification')


class FilterForm(forms.ModelForm):
    class Meta:
        model = Filter
        fields = ('name', 'description')
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Enter filter name', 'required': 'required'}),
            'description': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Description', 'style': 'resize:none;'})
        }


class FilterItemForm(forms.ModelForm):
    class Meta:
        model = FilterItem
        exclude = ()
        widgets = {
            'filter_type': forms.Select(attrs={'class': 'ui short search selection dropdown'}),
            'value': forms.TextInput(attrs={'placeholder': 'Filter value'})
        }
