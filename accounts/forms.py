from django import forms
from django.contrib.auth.forms import UserCreationForm

from accounts.models import User
from db.models import Section


class CustomUserCreationForm(UserCreationForm):
    """Form containing all necessary modifiable user fields.
    """
    email = forms.EmailField(
        max_length=254,
        required=True
    )
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(
            attrs={
                'placeholder': 'First Name'
            }
        )
    )
    last_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(
            attrs={
                'placeholder': 'Last Name'
            }
        )
    )

    class Meta:
        model = User
        fields = (
            'first_name',
            'last_name',
            'email',
        )

    def clean(self):
        # Check that no accounts with this email address (irrespective of case)
        cleaned_data = super(CustomUserCreationForm, self).clean()
        email = cleaned_data.get('email')
        if email and User.objects.filter(email__iexact=email).exists():
            self.add_error(
                'email', 'A user with that email address already exists.')
        return cleaned_data


class UpdateProfileForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True
        self.fields['default_section'].empty_label = 'Ask every time'

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'default_section')
