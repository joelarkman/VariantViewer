from django.views.generic import TemplateView
from django.shortcuts import render
from django.template.loader import render_to_string
from django.http import JsonResponse

from .forms import DocumentForm
from .models import Document


class IndexView(TemplateView):
    """
    Template View to display index page.
    """

    template_name = 'index.html'

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data()
        # base.html includes page_title by default
        context['page_title'] = 'Index'
        return context


class SearchView(TemplateView):
    """
    Template View to display search page.
    """

    template_name = 'search.html'

    def get_context_data(self, **kwargs):
        context = super(SearchView, self).get_context_data()
        # base.html includes page_title by default
        context['page_title'] = 'Search'
        return context


class SampleView(TemplateView):
    """
    Template View to display sample page.
    """

    template_name = 'sample.html'

    def get_context_data(self, **kwargs):
        context = super(SampleView, self).get_context_data()
        # base.html includes page_title by default
        context['page_title'] = 'Sample'
        return context


def load_variant_details(request):
    """
    AJAX view to load variant details. Database filtered for correct variant and its associated 
    evidence documents; data rendered using relevent template and sent back to sample page as
    a JSON response. 
    """

    data = dict()

    documents = Document.objects.all().order_by('-uploaded_at')

    form = DocumentForm()

    context = {'test': "this is a test",
               'form': form,
               'documents': documents}

    data['variant_details'] = render_to_string('variant-details.html',
                                               context,
                                               request=request)
    return JsonResponse(data)


def save_evidence(request):
    """
    AJAX view to facilitate jquery-file-upload save process. When recieve document from file uploader,
    save the file and retreive an updated set of evidence files. Return refreshed set of evidence 
    files to variant details page as a JSON response.
    """

    data = dict()

    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)

        if form.is_valid():

            # print(form.cleaned_data)

            form.save()

            documents = Document.objects.all().order_by('-uploaded_at')
            data['is_valid'] = True
            data['documents'] = render_to_string('includes/evidence.html',
                                                 {'documents': documents},
                                                 request=request)

            return JsonResponse(data)
