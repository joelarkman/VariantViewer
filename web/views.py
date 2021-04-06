from django.views.generic import TemplateView, ListView, DetailView
from django.shortcuts import render, get_object_or_404
from django.template.loader import render_to_string
from django.http import JsonResponse
from django.db.models import Q

from .models import Document

from .forms import DocumentForm


from db.models import Run, PipelineVersion, SamplesheetSample


class IndexView(ListView):
    """
    Template View to display index page.
    """
    model = Run
    template_name = 'index.html'
    paginate_by = 5

    def get_queryset(self):
        queryset = super().get_queryset()

        pipeline = self.request.GET.get('pipeline')
        if pipeline:
            if pipeline == 'all':
                pass
            else:
                queryset = queryset.filter(
                    pipeline_version__pipeline__id=pipeline)

        q = self.request.GET.get('q')
        if q:
            queryset = queryset.filter(
                Q(worksheet__icontains=q)
            )
        return queryset.order_by('-completed_at')

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data()
        # base.html includes page_title by default
        context['page_title'] = 'Index'

        pipeline = self.request.GET.get('pipeline')
        if pipeline:
            pipeline = pipeline.replace(" ", "+")
            context['pipeline'] = pipeline

        q = self.request.GET.get('q')
        if q:
            q = q.replace(" ", "+")
            context['searchq'] = q
            context['runs'] = Run.objects.filter(
                Q(worksheet__icontains=q)
            ).order_by(
                'pipeline_version__pipeline__name')
        else:
            context['runs'] = Run.objects.all().order_by(
                'pipeline_version__pipeline__name')

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
        context['pipelines'] = PipelineVersion.objects.all()
        return context


class SampleDetailsView(TemplateView):
    """
    Template View to display sample page.
    """

    # model = Sample
    # slug_field = 'slug'
    # slug_url_kwarg = 'slug'
    template_name = 'sample.html'
    # context_object_name = 'sample'

    def get_context_data(self, **kwargs):
        context = super(SampleDetailsView, self).get_context_data()
        # base.html includes page_title by default
        context['page_title'] = 'Sample'

        context['run'] = Run.objects.get(worksheet=self.kwargs['worksheet'])
        context['sample'] = SamplesheetSample.objects.get(
            sample_identifier=self.kwargs['sample'])

        context['vcf'] = 'test/123456-1-D00-00001-SYN_TSCPv2_S1.unified.annovar.wmrgldb.vcf.gz'
        context['tbi'] = 'test/123456-1-D00-00001-SYN_TSCPv2_S1.unified.annovar.wmrgldb.vcf.gz.tbi'

        context['bam'] = 'test/123456-1-D00-00001-SYN_TSCPv2_S1.bwa.drm.realn.sorted.bam'
        context['bai'] = 'test/123456-1-D00-00001-SYN_TSCPv2_S1.bwa.drm.realn.sorted.bam.bai'

        return context


def load_worksheet_details(request, pk):
    # Define a data storage dictionary.
    data = dict()

    run = get_object_or_404(Run, pk=pk)

    context = {
        'run': run}
    data['html_form'] = render_to_string(
        'includes/worksheet-detail.html', context, request=request)
    # Send data as JsonResponse.
    return JsonResponse(data)


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


# Temporary to explore jbrowse during development

class JbrowseTestingView(TemplateView):
    """
    Template View to display index page.
    """

    template_name = 'jbrowse-testing.html'

    def get_context_data(self, **kwargs):
        context = super(JbrowseTestingView, self).get_context_data()
        # base.html includes page_title by default
        context['page_title'] = 'Jbrowse Testing'

        context['vcf'] = 'test/123456-1-D00-00001-SYN_TSCPv2_S1.unified.annovar.wmrgldb.vcf.gz'
        context['tbi'] = 'test/123456-1-D00-00001-SYN_TSCPv2_S1.unified.annovar.wmrgldb.vcf.gz.tbi'

        context['bam'] = 'symtest/test-bam.bam'
        context['bai'] = 'symtest/test-bai.bai'

        return context
