from datetime import datetime
from hashlib import md5
import urllib

from accounts.forms import UpdateProfileForm
from django.contrib import messages
from django.views import View
from django.views.generic import TemplateView
from django.contrib.auth import login, update_session_auth_hash
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.mixins import UserPassesTestMixin
from django.views.generic import DetailView
from django.views.generic import FormView
from django.views.generic import CreateView
from django.views.generic import UpdateView
from django.views.generic.detail import SingleObjectMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.db import transaction
from django.urls import reverse, reverse_lazy

from accounts.models import User
from accounts.forms import CustomUserCreationForm
from django.contrib.auth.forms import PasswordChangeForm
from db.tasks import send_email


def redirect_params(url, params=None):
    response = redirect(url)
    if params:
        query_string = urllib.parse.urlencode(params)
        response['Location'] += '?' + query_string
    return response


class LogoutSuccessfulView(TemplateView):
    """
    Template View to display logout successful page.
    """

    template_name = 'registration/logout_successful.html'


class RegisterView(CreateView):
    form_class = CustomUserCreationForm
    template_name = 'registration/register.html'
    success_url = reverse_lazy('login')

    @transaction.atomic
    def post(self, request):
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.validate_hash = self.get_user_validate_hash(user)
            user.save()
            send_email.delay(
                email_type='validate_account',
                context={
                    'user': {
                        'model': ('accounts', 'User'),
                        'id': user.id
                    }
                },
                subject="Validate your VariantViewer account.",
                to=user.email
            )
            messages.info(
                request,
                "Thanks for registering. Please await an email to validate your"
                " account. If no email is received after 10 minutes, please"
                " first check your junk inbox before contacting Bioinformatics."
            )
            return redirect('login')
        else:
            return render(request, self.template_name, {'form': form})

    def get_user_validate_hash(self, user):
        m = md5()
        m.update(str(user.first_name + user.last_name +
                     str(datetime.now())).encode())
        return m.hexdigest()


class ValidateAccountView(UserPassesTestMixin, View):
    def test_func(self):
        user = self.user
        return not user.is_active

    def handle_no_permission(self):
        messages.error(
            self.request,
            "This validation link has expired as the associated user has already been activated."
        )
        return redirect('redirect')

    @transaction.atomic
    def get(self, request, *args, **kwargs):
        user = self.user
        user.is_active = True
        user.save()
        user.backend = 'django.contrib.auth.backends.ModelBackend'
        login(request, user)
        messages.info(
            request,
            f"{user.first_name}, your account has been activated and you are now logged in."
            "Please select a relevent section of the laboratory."
        )
        return redirect('redirect')

    @property
    def user(self):
        validate_hash = self.kwargs.get('validate_hash')
        user = User.objects.get(validate_hash=validate_hash)
        return user


class ProfileDisplay(LoginRequiredMixin, DetailView):
    """User profile view
    """
    model = User
    context_object_name = 'account'
    template_name = 'profile.html'

    def get_object(self):
        return get_object_or_404(User, id=self.request.user.id)

    def get_context_data(self, **kwargs):
        context = super(ProfileDisplay, self).get_context_data(**kwargs)
        account = self.get_object()

        context['form'] = UpdateProfileForm(instance=account)
        # context['history'] = get_user_audit_log(user=account)
        return context


class ProfileUpdate(LoginRequiredMixin, SingleObjectMixin, FormView):
    model = User
    context_object_name = 'account'
    form_class = UpdateProfileForm
    template_name = 'profile.html'

    def post(self, request, *args, **kwargs):

        params = {
            'next': self.request.GET.get('next')
        }

        self.object = self.get_object()
        form = UpdateProfileForm(request.POST, instance=self.object)
        print(form.errors)
        if form.is_valid():
            user = form.save()
            form.save()
            messages.success(request, "User profile successfully updated.")
            return redirect_params('profile', params)
        else:
            return render(request, self.template_name, {'form': form})

    def get_object(self):
        return get_object_or_404(User, id=self.request.user.id)

    def get_success_url(self):
        return reverse('profile')

    def get_context_data(self, **kwargs):
        context = super(ProfileUpdate, self).get_context_data(**kwargs)
        account = self.get_object()
        return context


class ProfileView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        view = ProfileDisplay.as_view()
        return view(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        view = ProfileUpdate.as_view()
        return view(request, *args, **kwargs)


class PasswordUpdate(LoginRequiredMixin, DetailView):
    model = User
    context_object_name = 'user'
    template_name = 'registration/change_password.html'

    @transaction.atomic
    def post(self, request):

        params = {
            'next': self.request.GET.get('next')
        }

        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important!
            messages.success(
                request, 'Your password was successfully updated!')
            return redirect_params('profile', params)
        else:
            return render(request, self.template_name, {'form': form})

    def get_object(self):
        return get_object_or_404(User, id=self.request.user.id)

    def get_context_data(self, **kwargs):
        context = super(PasswordUpdate, self).get_context_data(**kwargs)
        user = self.get_object()
        context['form'] = PasswordChangeForm(user)
        return context
