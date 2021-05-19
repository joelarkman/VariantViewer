from accounts.models import UserFilter
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, get_object_or_404
from django.template.loader import render_to_string
from django import forms
from django.http import JsonResponse
from django.shortcuts import redirect
from django.db.models import Q
from django.db import transaction

from db.utils.filter_utils import filter_variants, get_filters

from .models import Document, Filter, FilterItem

from .forms import CommentForm, DocumentForm, FilterForm, FilterItemForm

from db.models import ExcelReport, Gene, Run, PipelineVersion, SamplesheetSample, SampleTranscriptVariant, Section, Transcript, VCFFilter, VariantReportInfo


class RedirectView(TemplateView):

    template_name = 'section-select.html'

    def get_context_data(self, **kwargs):
        context = super(RedirectView, self).get_context_data()
        # base.html includes page_title by default
        section = Section.objects.all()
        context['page_title'] = 'Section select'
        context['section'] = section
        return context

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        elif self.kwargs['update'] or not request.user.default_section:
            return super(RedirectView, self).dispatch(request, *args, **kwargs)
        else:
            section = request.user.default_section.slug
            return redirect('home', section=section)

    def post(self, request, **kwargs):
        section = request.POST.get('section')
        default_choice = request.POST.get('default-choice')
        user = request.user

        if default_choice == 'set-default':
            user.default_section = Section.objects.get(slug=section)
            user.save()
        else:
            user.default_section = None
            user.save()

        return redirect('home', section=section)


class HomeView(LoginRequiredMixin, TemplateView):
    """
    Template View to display search page.
    """

    template_name = 'home.html'

    def get_context_data(self, **kwargs):
        context = super(HomeView, self).get_context_data()
        # base.html includes page_title by default
        section = Section.objects.get(slug=self.kwargs['section'])
        context['page_title'] = 'Home'
        context['section'] = section
        context['pipelines'] = PipelineVersion.objects.filter(
            pipeline__pipelinesection__section=section, pipeline__pipelinesection__default=True)

        return context


class SearchView(LoginRequiredMixin, TemplateView):
    """
    Template View to display search page.
    """

    template_name = 'search.html'

    def get_context_data(self, **kwargs):
        context = super(SearchView, self).get_context_data()
        # base.html includes page_title by default
        section = Section.objects.get(slug=self.kwargs['section'])
        context['page_title'] = 'Search'
        context['section'] = section
        context['pipelines'] = PipelineVersion.objects.filter(
            pipeline__pipelinesection__section=section, pipeline__pipelinesection__default=True)
        return context


class SampleDetailsView(LoginRequiredMixin, TemplateView):
    """
    Template View to display sample page.
    """

    template_name = 'sample.html'

    def get_context_data(self, **kwargs):
        context = super(SampleDetailsView, self).get_context_data()
        # base.html includes page_title by default
        ss_sample = SamplesheetSample.objects.get(
            sample_identifier=self.kwargs['sample'])

        section = ss_sample.sample.section

        run = Run.objects.get(worksheet=self.kwargs['worksheet'])

        context['page_title'] = f"{ss_sample.sample_identifier} ({ss_sample.sample.lab_no})"
        context['section'] = section
        context['run'] = run
        context['ss_sample'] = ss_sample

        # filters = get_filters(ss_sample.sample, run, user=self.request.user)
        # filtered_variants = filter_variants(
        #     ss_sample.sample, run, filter=filters.get('active_filter'))

        # context['variants'] = filtered_variants

        # context['filters'] = filters

        # context['excelreport'] = ExcelReport.objects.get(
        #     run=run, sample=ss_sample.sample)

        # Load files for jbrowse
        context['vcf'] = 'test/123456-1-D00-00001-SYN_TSCPv2_S1.unified.annovar.wmrgldb.vcf.gz'
        context['tbi'] = 'test/123456-1-D00-00001-SYN_TSCPv2_S1.unified.annovar.wmrgldb.vcf.gz.tbi'

        context['bam'] = 'test/123456-1-D00-00001-SYN_TSCPv2_S1.bwa.drm.realn.sorted.bam'
        context['bai'] = 'test/123456-1-D00-00001-SYN_TSCPv2_S1.bwa.drm.realn.sorted.bam.bai'

        # Exome test
        # context['vcf'] = 'example.nosync/exome.vcf.gz'
        # context['tbi'] = 'example.nosync/exome_vcf.tbi'
        # context['bam'] = 'example.nosync/exome.bam'
        # context['bai'] = 'example.nosync/exome.bai'

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


def modify_filters(request, run, ss_sample, filter=None):
    """
    AJAX view to create, modify or switch between filter presets using formset and custom filter utility functions.
    """

    data = dict()
    context = dict()

    run = Run.objects.get(id=run)
    ss_sample = SamplesheetSample.objects.get(
        id=ss_sample)
    vcf = ss_sample.sample.vcfs.get(run=run)

    VRI_tags = VariantReportInfo.objects.filter(
        variant_report__vcf=vcf).values_list('tag', 'tag').distinct()

    VRI_tags = [('qual', 'qual'), ('depth', 'depth')] + list(VRI_tags)

    VRI_tags.sort(key=lambda t: tuple(t[0].lower()))

    def populate_field_choices(field, **kwargs):
        if field.name == 'field':
            return forms.CharField(widget=forms.Select(choices=VRI_tags, attrs={'class': 'ui short search selection dropdown filter-dropdown'}))
        return field.formfield(**kwargs)

    FilterItemFormSet = forms.inlineformset_factory(Filter, FilterItem,
                                                    form=FilterItemForm, extra=0, can_delete=True, formfield_callback=populate_field_choices)

    # Load all relevent filters to display as options in the form.
    filters = get_filters(
        ss_sample.sample, run, user=request.user)

    try:
        instance = Filter.objects.get(id=filter)
    except:
        instance = None

    if request.method == "POST":
        form = FilterForm(request.POST, instance=instance)

        if form.is_valid():
            applied_filter = form.save()

            # If applying pipeline preset
            if applied_filter == filters.get('pipeline_default_filter'):
                # deselect all user presets
                for userfilter in UserFilter.objects.filter(user=request.user, filter__vcf=vcf):
                    userfilter.selected = False
                    userfilter.save()
            else:
                # If applying a user preset.

                # Associate this filter with VCF if it hasnt before.
                if not VCFFilter.objects.filter(vcf=vcf, filter=applied_filter).exists():
                    vf1 = VCFFilter(vcf=vcf, filter=applied_filter)
                    vf1.save()

                # Associate this filter with logged in User if it hasnt before.
                if not UserFilter.objects.filter(user=request.user, filter=applied_filter).exists():
                    uf1 = UserFilter(user=request.user, filter=applied_filter)
                    uf1.save()

                # Deselect all other user presets and select this one.
                for userfilter in UserFilter.objects.filter(user=request.user, filter__vcf=vcf):
                    if userfilter.filter == applied_filter:
                        userfilter.selected = True
                        userfilter.save()
                    else:
                        userfilter.selected = False
                        userfilter.save()

            # Save any changes to the filter items
            formset = FilterItemFormSet(
                request.POST, request.FILES, instance=applied_filter)

            try:
                # Try and filter variants using selected filter. If filter function fails then any changes to formset will be rolled back.
                with transaction.atomic():
                    if formset.is_valid():
                        formset.save()

                    filters = get_filters(
                        ss_sample.sample, run, user=request.user)
                    filtered_variants = filter_variants(
                        ss_sample.sample, run, filter=filters.get('active_filter'))

                    data['form_is_valid'] = True

                    data['variant_list'] = render_to_string('includes/variant-list.html',
                                                            {'run': run,
                                                             'ss_sample': ss_sample,
                                                             'variants': filtered_variants},
                                                            request=request)

                    data['active_filters'] = render_to_string('includes/active-filters.html',
                                                              {'run': run,
                                                               'ss_sample': ss_sample,
                                                               'filters': filters},
                                                              request=request)
            except:
                data['form_is_valid'] = False

                context.update({'invalid_filters': True})

    else:
        form = FilterForm(instance=instance)
        formset = FilterItemFormSet(instance=instance)

    context.update({'run': run,
                    'ss_sample': ss_sample,
                    'filter_instance': instance,
                    'filters': filters,
                    'form': form,
                    'formset': formset})

    data['html_form'] = render_to_string('includes/modify-filters.html',
                                         context,
                                         request=request)
    return JsonResponse(data)


def load_variant_list(request, run, ss_sample):
    """
    AJAX view to load variant list.
    """

    data = dict()
    run = Run.objects.get(id=run)
    ss_sample = SamplesheetSample.objects.get(
        id=ss_sample)

    filters = get_filters(ss_sample.sample, run, user=request.user)

    filtered_variants = filter_variants(
        ss_sample.sample, run, filter=filters.get('active_filter'))

    data['variant_list'] = render_to_string('includes/variant-list.html',
                                            {'run': run,
                                             'ss_sample': ss_sample,
                                             'variants': filtered_variants},
                                            request=request)

    data['active_filters'] = render_to_string('includes/active-filters.html',
                                              {'run': run,
                                               'ss_sample': ss_sample,
                                               'filters': filters},
                                              request=request)

    return JsonResponse(data)


def load_variant_details(request, run, stv):
    """
    AJAX view to load variant details. Database filtered for correct variant and its associated
    evidence documents; data rendered using relevent template and sent back to sample page as
    a JSON response.
    """

    data = dict()

    run = Run.objects.get(id=run)
    stv = SampleTranscriptVariant.objects.get(id=stv)
    variant_report = stv.get_variant_report(run=run)
    documents = stv.evidence_files.order_by('-date_created')
    related_stvs = SampleTranscriptVariant.objects.filter(
        sample_variant__variant=stv.sample_variant.variant, comments__classification=0)

    form = DocumentForm()

    context = {'run': run,
               'stv': stv,
               'variant_report': variant_report,
               'form': form,
               'documents': documents,
               'related_stvs': related_stvs}

    data['variant_details'] = render_to_string('variant-details.html',
                                               context,
                                               request=request)
    return JsonResponse(data)


def pin_variant(request, run, stv):
    """
    AJAX view to pin variant.
    """

    data = dict()
    run = Run.objects.get(id=run)
    stv = SampleTranscriptVariant.objects.get(id=stv)
    ss_sample = SamplesheetSample.objects.get(
        sample=stv.sample_variant.sample.id)

    filters = get_filters(ss_sample.sample, run, user=request.user)

    filtered_variants = filter_variants(
        ss_sample.sample, run, filter=filters.get('active_filter'))

    ischecked = request.GET.get('ischecked')

    if ischecked == 'true':
        stv.pinned = True
        stv.save()
    elif ischecked == 'false':
        stv.pinned = False
        stv.save()

    data['variant_list'] = render_to_string('includes/variant-list.html',
                                            {'run': run,
                                             'ss_sample': ss_sample,
                                             'variants': filtered_variants},
                                            request=request)
    return JsonResponse(data)


def update_selected_transcript(request, run, ss_sample, transcript):
    """
    AJAX view to view all available transcripts for a sequenced gene, preview variants identified for each one, and set one as selected for a given sample.
    """

    run = Run.objects.get(id=run)
    current_transcript = Transcript.objects.get(id=transcript)
    ss_sample = SamplesheetSample.objects.get(
        id=ss_sample)

    filters = get_filters(ss_sample.sample, run, user=request.user)

    filtered_variants = filter_variants(
        ss_sample.sample, run, filter=filters.get('active_filter'))

    variant_containing_transcripts = SampleTranscriptVariant.objects.filter(sample_variant__sample=ss_sample.sample,
                                                                            sample_variant__variant__variantreport__vcf=ss_sample.sample.vcfs.get(
                                                                                run=run),
                                                                            transcript__gene=current_transcript.gene).order_by('transcript__gene__hgnc_name')

    data = dict()

    if request.method == 'POST':
        data['form_is_valid'] = True
        new_transcript = Transcript.objects.get(
            id=request.POST.get('selected-transcript'))

        # Temporary implementation until unique-together has been added:
        for stv in SampleTranscriptVariant.objects.filter(sample_variant__sample=ss_sample.sample, transcript__gene=new_transcript.gene):
            if stv.transcript == new_transcript:
                stv.selected = True
                stv.save()
            else:
                stv.selected = False
                stv.save()

        data['variant_list'] = render_to_string('includes/variant-list.html',
                                                {'run': run,
                                                 'ss_sample': ss_sample,
                                                 'variants': filtered_variants},
                                                request=request)

    context = {'run': run,
               'ss_sample': ss_sample,
               'selected_transcript': current_transcript,
               'variant_containing_transcripts': variant_containing_transcripts}

    data['html_form'] = render_to_string('includes/update-transcript.html',
                                         context,
                                         request=request)
    return JsonResponse(data)


def comment_update_or_create(request, stv):
    """
    AJAX view to facilitate the creation or update of a single comment object for each STV.  
    """
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


def delete_evidence(request, document):
    """
    AJAX view to facilitate the deletion of an evidence object associated with a particular STV.
    """

    data = dict()
    document = Document.objects.get(id=document)
    stv = document.sample_transcript_variant

    if request.method == 'POST':
        document.delete()

        documents = stv.evidence_files.order_by('-date_created')
        data['is_valid'] = True
        data['documents'] = render_to_string('includes/evidence.html',
                                             {'documents': documents},
                                             request=request)
    else:
        context = {'document': document}
        data['html_form'] = render_to_string('includes/delete-evidence.html',
                                             context,
                                             request=request
                                             )
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
