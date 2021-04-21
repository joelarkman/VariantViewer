from django.views.generic import TemplateView, ListView, DetailView
from django.shortcuts import render, get_object_or_404
from django.template.loader import render_to_string
from django.http import JsonResponse
from django.db.models import Q

from .models import Comment, Document

from .forms import CommentForm, DocumentForm


from db.models import ExcelReport, Gene, Run, PipelineVersion, Sample, SamplesheetSample, SampleTranscriptVariant, Transcript


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

    template_name = 'sample.html'

    def get_context_data(self, **kwargs):
        context = super(SampleDetailsView, self).get_context_data()
        # base.html includes page_title by default

        sample = SamplesheetSample.objects.get(
            sample_identifier=self.kwargs['sample'])

        run = Run.objects.get(worksheet=self.kwargs['worksheet'])

        context['run'] = run
        context['sample'] = sample
        context['page_title'] = f"{sample.sample_identifier} ({sample.sample.lab_no})"
        context['excelreport'] = ExcelReport.objects.get(
            run=run, sample=sample.sample)

        # Load files for jbrowse
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


def load_variant_details(request, variant):
    """
    AJAX view to load variant details. Database filtered for correct variant and its associated 
    evidence documents; data rendered using relevent template and sent back to sample page as
    a JSON response. 
    """

    data = dict()

    stv = SampleTranscriptVariant.objects.get(id=variant)
    documents = stv.evidence_files.order_by('-date_created')

    form = DocumentForm()

    context = {'stv': stv,
               'form': form,
               'documents': documents}

    data['variant_details'] = render_to_string('variant-details.html',
                                               context,
                                               request=request)
    return JsonResponse(data)


def pin_variant(request, stv):
    """
    AJAX view to pin variant. 
    """

    data = dict()
    stv = SampleTranscriptVariant.objects.get(id=stv)
    ischecked = request.GET.get('ischecked')

    if ischecked == 'true':
        stv.pinned = True
        stv.save()
    else:
        stv.pinned = False
        stv.save()

    data['variant_list'] = render_to_string('includes/variant-list.html',
                                            {'sample': SamplesheetSample.objects.get(
                                                sample=stv.sample_variant.sample)},
                                            request=request)
    return JsonResponse(data)


def update_selected_transcript(request, sample, transcript):
    """
    AJAX view to view all available transcripts for a sequenced gene, preview variants identified for each one, and set one as selected for a given sample.
    """
    current_transcript = Transcript.objects.get(id=transcript)
    sample = Sample.objects.get(id=sample)
    data = dict()

    if request.method == 'POST':
        data['form_is_valid'] = True
        new_transcript = Transcript.objects.get(
            id=request.POST.get('selected-transcript'))

        # Temporary implementation until unique-together has been added:
        for stv in SampleTranscriptVariant.objects.filter(sample_variant__sample=sample, transcript__gene=new_transcript.gene):
            if stv.transcript == new_transcript:
                stv.selected = True
                stv.save()
            else:
                stv.selected = False
                stv.save()

        data['variant_list'] = render_to_string('includes/variant-list.html',
                                                {'sample': SamplesheetSample.objects.get(
                                                    sample=sample)},
                                                request=request)

    context = {'sample': SamplesheetSample.objects.get(sample=sample),
               'selected_transcript': current_transcript,
               'variant_containing_transcripts': SampleTranscriptVariant.objects.filter(sample_variant__sample=sample, transcript__gene=current_transcript.gene).order_by('transcript__gene__hgnc_name')}

    data['html_form'] = render_to_string('includes/update-transcript.html',
                                         context,
                                         request=request)
    return JsonResponse(data)


def comment_update_or_create(request, stv):

    data = dict()
    stv = SampleTranscriptVariant.objects.get(id=stv)

    try:
        comment = stv.comments.last()
    except:
        comment = None

    if request.method == 'POST':
        form = CommentForm(request.POST, instance=comment)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.sample_transcript_variant = stv
            comment.save()

            data['form_is_valid'] = True
            data['html_comment_display'] = render_to_string('includes/comment-display.html', {
                'stv': stv
            })
            data['html_classification'] = render_to_string('includes/classification.html', {
                'stv': stv
            })
        else:
            data['form_is_valid'] = False
    else:
        form = CommentForm(instance=comment)

    context = {'form': form,
               'stv': stv}
    data['html_form'] = render_to_string('includes/comment-form.html',
                                         context,
                                         request=request
                                         )
    return JsonResponse(data)


def save_evidence(request, stv):
    """
    AJAX view to facilitate jquery-file-upload save process. When recieve document from file uploader,
    save the file and retreive an updated set of evidence files. Return refreshed set of evidence 
    files to variant details page as a JSON response.
    """

    data = dict()
    stv = SampleTranscriptVariant.objects.get(id=stv)

    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)

        if form.is_valid():

            evidence_file = form.save(commit=False)
            evidence_file.sample_transcript_variant = stv
            evidence_file.save()

            documents = stv.evidence_files.order_by('-date_created')
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

        context['genes'] = Gene.objects.all()

        context['vcf'] = 'test/123456-1-D00-00001-SYN_TSCPv2_S1.unified.annovar.wmrgldb.vcf.gz'
        context['tbi'] = 'test/123456-1-D00-00001-SYN_TSCPv2_S1.unified.annovar.wmrgldb.vcf.gz.tbi'

        context['bam'] = 'symtest/test-bam.bam'
        context['bai'] = 'symtest/test-bai.bai'

        return context
