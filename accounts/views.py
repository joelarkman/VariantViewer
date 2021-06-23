from accounts.forms import UpdateProfileForm
from django.views import View
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import DetailView
from django.views.generic import FormView
from django.views.generic.detail import SingleObjectMixin
from django.shortcuts import get_object_or_404

from accounts.models import User


class LogoutSuccessfulView(TemplateView):
    """
    Template View to display logout successful page.
    """

    template_name = 'registration/logout_successful.html'


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
        self.object = self.get_object()
        form = UpdateProfileForm(request.POST, instance=self.object)
        if form.is_valid():
            form.save()
            form.save_m2m()
            messages.success(request, "User profile successfully updated.")
        return redirect('profile', username=kwargs.get('username'))

    def get_object(self):
        return get_object_or_404(User, username=self.kwargs.get('username'))

    def get_success_url(self):
        return reverse('profile', kwargs={'username': self.object.username})

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
