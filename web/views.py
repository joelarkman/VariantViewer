from accounts.models import UserFilter
from django.views.generic import View, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, get_object_or_404
from django.template.loader import render_to_string
from django import forms
from django.http import JsonResponse, HttpResponse
from django.shortcuts import redirect
from django.db.models import Q
from django.db import transaction

import statistics

from db.utils.filter_utils import filter_variants, get_filters, apply_variant_cache, context_to_string, string_to_context
from db.utils.model_utils import mode

from .models import Comment, Document, Filter, FilterItem, Report
from .utils.model_utils import LastUpdated
from .utils.report_utils import get_report_results, render_to_pdf, create_report_context, update_selected_results

from .forms import CommentForm, DocumentForm, FilterForm, FilterItemForm, ReportForm

from db.models import ExcelReport, Gene, Pipeline, Run, PipelineVersion, SamplesheetSample, SampleTranscriptVariant, Section, Transcript, VCFFilter, VariantReportInfo


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
        context['pipelines'] = Pipeline.objects.filter(
            pipelinesection__section=section, pipelinesection__default=True)
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
        context['pipelines'] = Pipeline.objects.filter(
            pipelinesection__section=section, pipelinesection__default=True)
        return context


class SampleDetailsView(LoginRequiredMixin, TemplateView):
    """
    Template View to display sample page.
    """

    template_name = 'sample.html'

    def get_context_data(self, **kwargs):
        context = super(SampleDetailsView, self).get_context_data()
        # base.html includes page_title by default
        # ss_sample = SamplesheetSample.objects.get(
        #     sample_identifier=self.kwargs['sample'])

        ss_sample = SamplesheetSample.objects.get(
            sample__lab_no=self.kwargs['sample'], samplesheet__latest_run__worksheet=self.kwargs['worksheet'])

        section = ss_sample.sample.section

        pipeline_version = self.kwargs['pipeline_version'].split('-')

        run = Run.objects.get(
            worksheet=self.kwargs['worksheet'], pipeline_version__pipeline__name__iexact=pipeline_version[0], pipeline_version__version=pipeline_version[1])

        context['page_title'] = f"{ss_sample.sample.lab_no} ({run.worksheet})"
        context['section'] = section
        context['run'] = run
        context['ss_sample'] = ss_sample

        # Load files for jbrowse
        context['vcf'] = ss_sample.sample.vcfs.get(run=run)
        context['bam'] = ss_sample.sample.bams.get(
            run=run, path__contains="realn")

        context['cov_thresholds'] = ExcelReport.objects.get(
            run=run, sample=ss_sample.sample).genereport_set.first().cov_thresholds

        return context


def run_first_check(request, pk):
    # Define a data storage dictionary.
    data = dict()

    run = get_object_or_404(Run, pk=pk)

    if request.method == 'POST':
        qc_status = request.POST.get('qc_status')

        if qc_status:
            data['form_is_valid'] = True

            if qc_status == 'pass':
                run.qc_status = 1
            else:
                run.qc_status = 2

            run.save()
        else:
            data['form_is_valid'] = False

    context = {
        'run': run}
    data['html_form'] = render_to_string(
        'includes/run-first-check.html', context, request=request)
    # Send data as JsonResponse.
    return JsonResponse(data)


def run_second_check(request, pk):
    # Define a data storage dictionary.
    data = dict()

    run = get_object_or_404(Run, pk=pk)
    last_updated = LastUpdated(run, 'qc_status')

    if request.method == 'POST':
        if not last_updated['fields']['qc_status']['user'] == request.user:
            qc_status_second_check = request.POST.get(
                'qc_status_second_check')

            if qc_status_second_check:
                data['form_is_valid'] = True

                if qc_status_second_check == 'accept':
                    run.checked = True
                else:
                    run.qc_status = 0

                run.save()
        else:
            data['form_is_valid'] = False

    context = {
        'run': run,
        'last_updated': last_updated}
    data['html_form'] = render_to_string(
        'includes/run-second-check.html', context, request=request)
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

    VRI_tags = [('qual', 'qual'), ('depth', 'depth'),
                ('impact', 'impact'), ('consequence', 'consequence')] + list(VRI_tags)

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
                    data['variant_cache'] = filtered_variants.get(
                        'variant_cache')

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
    variant_cache = request.GET.get('variant_cache')

    run = Run.objects.get(id=run)
    ss_sample = SamplesheetSample.objects.get(
        id=ss_sample)

    filters = get_filters(ss_sample.sample, run, user=request.user)

    if variant_cache:
        filtered_variants = apply_variant_cache(
            ss_sample.sample, run, variant_cache)
    else:
        filtered_variants = filter_variants(
            ss_sample.sample, run, filter=filters.get('active_filter'))
        data['variant_cache'] = filtered_variants.get('variant_cache')

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


def refresh_classification_indicators(request, run):
    """
    AJAX view to update variant list classification indicators.
    """

    data = dict()
    run = Run.objects.get(id=run)

    if request.method == 'POST':
        stvs = request.POST.getlist('elements[]')

        values = {}
        for stv in stvs:
            instance = SampleTranscriptVariant.objects.get(id=stv)

            try:
                classification = instance.comment.get_classification(run)
                if classification['classification'] == 'Unclassified':
                    css = 'blue outline'
                else:
                    css = classification['colour']

            except:
                classified_instances = SampleTranscriptVariant.objects.filter(
                    sample_variant__variant=instance.sample_variant.variant, transcript=instance.transcript).exclude(id=instance.id).exclude(comment__classification__isnull=True)
                indicator_list = [
                    stv.comment.get_classification(run)['colour'] for stv in classified_instances]

                if indicator_list:
                    if len(indicator_list) == 1:
                        css = indicator_list[0] + ' outline'
                    else:
                        css = statistics.mode(
                            indicator_list) + ' outline'
                else:
                    css = 'blue outline'

            values.update({stv: css})

        data['values'] = values

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
    documents = stv.evidence_files.filter(
        archived=False).order_by('-date_modified')
    archived_documents = stv.evidence_files.filter(
        archived=True).order_by('-date_modified')

    try:
        stv_classification = stv.comment.get_classification(run)
    except:
        stv_classification = None

    form = DocumentForm()

    gnomad_variant = f'{stv.sample_variant.variant.chrom}-{stv.sample_variant.variant.pos}-{stv.sample_variant.variant.ref}-{stv.sample_variant.variant.alt}'
    gnomad_link = f'https://gnomad.broadinstitute.org/variant/{gnomad_variant}?dataset=gnomad_r3'

    context = {'run': run,
               'stv': stv,
               'stv_classification': stv_classification,
               'variant_report': variant_report,
               'gnomad_link': gnomad_link,
               'form': form,
               'documents': documents,
               'archived_documents': archived_documents}

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

    if request.method == 'POST':
        ischecked = request.POST.get('ischecked')

        if ischecked == 'true':
            stv.pinned = True
            stv.save()
        elif ischecked == 'false':
            stv.pinned = False
            stv.save()

    return JsonResponse(data)


def update_selected_transcript(request, run, ss_sample, transcript):
    """
    AJAX view to view all available transcripts for a sequenced gene, preview variants identified for each one, and set one as selected for a given sample.
    """

    run = Run.objects.get(id=run)
    current_transcript = Transcript.objects.get(id=transcript)
    ss_sample = SamplesheetSample.objects.get(
        id=ss_sample)

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

    context = {'run': run,
               'ss_sample': ss_sample,
               'selected_transcript': current_transcript,
               'variant_containing_transcripts': variant_containing_transcripts}

    data['html_form'] = render_to_string('includes/update-transcript.html',
                                         context,
                                         request=request)
    return JsonResponse(data)


def comment_update_or_create(request, run, stv):
    """
    AJAX view to facilitate the creation or update of a single comment object for each STV.
    """
    data = dict()
    run = Run.objects.get(id=run)
    stv = SampleTranscriptVariant.objects.get(id=stv)

    try:
        comment = stv.comment
    except:
        comment = None

    if request.method == 'POST':
        form = CommentForm(request.POST, instance=comment,
                           pipeline_version=run.pipeline_version)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.sample_transcript_variant = stv
            comment.save()

            data['form_is_valid'] = True
            data['html_comment_display'] = render_to_string('includes/comment-display.html', {
                'stv': stv
            })
            data['html_classification'] = render_to_string('includes/classification.html', {
                'stv': stv,
                'stv_classification': stv.comment.get_classification(run)
            })
        else:
            data['form_is_valid'] = False
    else:
        form = CommentForm(
            instance=comment, pipeline_version=run.pipeline_version)

    context = {'form': form,
               'stv': stv,
               'run': run}
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

            documents = stv.evidence_files.filter(
                archived=False).order_by('-date_modified')
            archived_documents = stv.evidence_files.filter(
                archived=True).order_by('-date_modified')
            data['is_valid'] = True
            data['documents'] = render_to_string('includes/evidence.html',
                                                 {'documents': documents,
                                                  'archived_documents': archived_documents},
                                                 request=request)

            return JsonResponse(data)


def archive_evidence(request, document):
    """
    AJAX view to facilitate the archiving of a document associated with a particular STV.
    """

    data = dict()
    document = Document.objects.get(id=document)
    stv = document.sample_transcript_variant

    if request.method == 'POST':
        document.archived = True
        document.save()

        documents = stv.evidence_files.filter(
            archived=False).order_by('-date_created')
        archived_documents = stv.evidence_files.filter(
            archived=True).order_by('-date_created')
        data['is_valid'] = True
        data['documents'] = render_to_string('includes/evidence.html',
                                             {'documents': documents,
                                                 'archived_documents': archived_documents},
                                             request=request)
    else:
        context = {'document': document}
        data['html_form'] = render_to_string('includes/archive-evidence.html',
                                             context,
                                             request=request
                                             )
    return JsonResponse(data)


def load_previous_evidence(request, run, current_stv, previous_stv):
    """
    AJAX view to facilitate the view of previous evidence
    """

    data = dict()
    run = Run.objects.get(id=run)
    current_stv = SampleTranscriptVariant.objects.get(id=current_stv)
    previous_stv = SampleTranscriptVariant.objects.get(id=previous_stv)
    previous_documents = previous_stv.evidence_files.filter(
        archived=False).order_by('-date_created')

    if previous_stv.comment:
        previous_stv_classification = previous_stv.comment.get_classification(
            run)
    else:
        previous_stv_classification = None

    if request.method == 'POST':

        classification = request.POST.get('classification')
        if classification:
            previous_comment = Comment.objects.get(id=classification)

            added_comment, created = Comment.objects.update_or_create(
                sample_transcript_variant=current_stv,
                defaults={'comment': previous_comment.comment,
                          'classification': previous_comment.classification})

        for document in request.POST.getlist('documents'):
            document = Document.objects.get(id=document)
            added_document, created = Document.objects.update_or_create(sample_transcript_variant=current_stv,
                                                                        document=document.document,
                                                                        description=document.description,
                                                                        defaults={'archived': False})

        documents = current_stv.evidence_files.filter(
            archived=False).order_by('-date_modified')
        archived_documents = current_stv.evidence_files.filter(
            archived=True).order_by('-date_modified')

        data['is_valid'] = True
        data['documents'] = render_to_string('includes/evidence.html',
                                             {'documents': documents,
                                                 'archived_documents': archived_documents},
                                             request=request)
        data['html_comment_display'] = render_to_string('includes/comment-display.html', {
            'stv': current_stv
        })
        data['html_classification'] = render_to_string('includes/classification.html', {
            'stv': current_stv,
            'stv_classification': current_stv.comment.get_classification(run)
        })
    else:
        context = {'run': run,
                   'current_stv': current_stv,
                   'previous_stv': previous_stv,
                   'previous_stv_classification': previous_stv_classification,
                   'previous_documents': previous_documents}
        data['html_form'] = render_to_string('includes/previous-evidence.html',
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

        context['section'] = Section.objects.first()

        context['genes'] = Gene.objects.all()

        context['vcf'] = 'test/123456-1-D00-00001-SYN_TSCPv2_S1.unified.annovar.wmrgldb.vcf.gz'
        context['tbi'] = 'test/123456-1-D00-00001-SYN_TSCPv2_S1.unified.annovar.wmrgldb.vcf.gz.tbi'

        context['bam'] = 'symtest/test-bam.bam'
        context['bai'] = 'symtest/test-bai.bai'

        return context


def GenerateReport(request):
    # Retrieve context string query parameter from url and convert back to python dict using custom function.
    context_string = request.GET.get('context')
    context = string_to_context(context_string)

    # Call custom utility function to generate pdf using template and contexct dict.
    pdf = render_to_pdf('pdf/new.html', context)
    if pdf:
        response = HttpResponse(pdf, content_type='application/pdf')
        filename = "%s.pdf" % (context['title'])
        content = "inline; filename=%s;" % (filename)
        download = request.GET.get("download")
        if download:
            content = "attachment; filename=%s" % (filename)
        response['Content-Disposition'] = content
        return response
    return HttpResponse("Not found")


def report_update_or_create(request, run, ss_sample, report=None):
    """
    AJAX view to create, update or delete reports.
    """

    data = dict()
    context = dict()

    # Load sample context
    ss_sample = SamplesheetSample.objects.get(id=ss_sample)
    run = Run.objects.get(id=run)
    reports = Report.objects.filter(
        run=run, samplesheetsample=ss_sample).order_by('-date_modified')

    if report == 'new':
        # Create a blank instance if making a new report
        instance = None
    else:
        try:
            # Load specific report instance if provided
            instance = Report.objects.get(id=report)
        except:
            # Load latest report if none provided
            if Report.objects.filter(run=run, samplesheetsample=ss_sample).exists():
                instance = Report.objects.filter(
                    run=run, samplesheetsample=ss_sample).last()
            else:
                # Load no report if none provided and a relevent one does not yet exist.
                instance = None

    if instance:
        report_context = instance.data
        instance_status = instance.id
    else:
        report_context = None
        instance_status = 'new'

    if request.method == "POST":
        form = ReportForm(request.POST, instance=instance)

        if form.is_valid():
            instance = form.save(commit=False)
            instance.run = run
            instance.samplesheetsample = ss_sample

            selected_stvs = request.POST.getlist('selected-stvs')

            if request.POST.get('commit') == 'true':
                commit = True
                instance.save()
            else:
                commit = False

            instance.data = create_report_context(run, ss_sample,
                                                  selected_stvs, instance,
                                                  request.user, commit)

            if request.POST.get('refresh-results'):
                # If refreshing report tab, generate report data using values from PDF
                # already on the page (sent via hidden field) not values in form.
                report_context_string = request.POST.get('refresh-results')
                report_context_data = string_to_context(report_context_string)
            else:
                report_context_data = instance.data
                report_context_string = context_to_string(report_context_data)

            report_results = get_report_results(run, ss_sample,
                                                request.user, report_context_data)

            if request.POST.get('refresh-results'):
                data['refresh'] = True
                report_results = update_selected_results(
                    report_results, selected_stvs)

            if commit:
                instance.save()
                instance_status = instance.id

            if report_context_data['preview']:
                context.update({'preview': True})
                context.update({'unsaved_name': instance.data['title']})

            data['is_valid'] = True
    else:
        # Populate report form using existing or blank instance.
        form = ReportForm(instance=instance)

        report_results = get_report_results(
            run, ss_sample, request.user, context=report_context)

        if not instance:
            auto_selected_stvs = [
                stv['id'] for stv in report_results['stvs'] if stv['selected'] == True]
            report_context = create_report_context(
                run, ss_sample, auto_selected_stvs, user=request.user)
            context.update({'default_name': report_context['title']})

        if report == 'default' and not instance:
            data['show_new_button'] = True
            context.update({'show_new_button': True})

        # Use custom function to convert context needed to generate report to a URL compatible string.
        report_context_string = context_to_string(report_context)

    context.update({'run': run,
                    'ss_sample': ss_sample,
                    'reports': reports,
                    'report_results': report_results,
                    'form': form,
                    'report_context_string': report_context_string,
                    'instance_status': instance_status,
                    'report_instance': instance})

    # Render report template using established context.
    data['report_container'] = render_to_string('includes/report-container.html',
                                                context,
                                                request=request)

    # JS will populate html object in template with URL that will call GenerateReport view using report_context_string.
    data['report_context_string'] = report_context_string

    return JsonResponse(data)


def GenerateVariantDiagram(request):

    image = open(
        'web/static/dependencies/lollipop/TP53.svg', 'rb')

    return HttpResponse(image, content_type="image/svg+xml")
