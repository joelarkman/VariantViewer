from django import forms
from django.forms import inlineformset_factory, BaseInlineFormSet
from .models import Comment, Document, Filter, FilterItem, Report


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
        fields = ('name', 'description', 'match')
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Enter filter name', 'required': 'required'}),
            'description': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Enter filter description (optional)', 'style': 'resize:none;'}),
            'match': forms.Select(attrs={'class': 'ui mini selection dropdown filter-dropdown'})
        }


class FilterItemForm(forms.ModelForm):
    class Meta:
        model = FilterItem
        exclude = ()
        widgets = {
            'filter_type': forms.Select(attrs={'class': 'ui short search selection dropdown filter-dropdown'}),
            'value': forms.TextInput(attrs={'placeholder': 'Filter value'})
        }


class ReportForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ('name', 'summary', 'recommendations')
