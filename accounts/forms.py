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


class UpdateProfileForm(CustomUserCreationForm):
    """Form allowing editing of certain user fields - not username.
    Since this inherits from a UserCreationForm (grandparent) must not provide
    password fields either which are included by default.
    """

    def __init__(self, *args, **kwargs):
        super(UpdateProfileForm, self).__init__(*args, **kwargs)
        del self.fields['password1']
        del self.fields['password2']

    default_section = forms.ModelChoiceField(
        queryset=Section.objects.all(),
        widget=forms.Select(
            attrs={
                'class': 'ui dropdown'
            }
        )
    )

    class Meta:
        model = User
        fields = (
            'first_name',
            'last_name',
            'default_section'
        )
