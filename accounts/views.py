from django.views.generic import TemplateView


class LogoutSuccessfulView(TemplateView):
    """
    Template View to display logout successful page.
    """

    template_name = 'registration/logout_successful.html'
