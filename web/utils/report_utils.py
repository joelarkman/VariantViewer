from django.db.models.aggregates import Count
from db.models import SampleTranscriptVariant
from io import BytesIO
from django.http import HttpResponse
from django.template.loader import get_template
import datetime
import urllib.parse
import json

from db.utils.filter_utils import filter_variants, get_filters
from web.models import Report

from xhtml2pdf import pisa


def render_to_pdf(template_src, context_dict={}):
    template = get_template(template_src)
    html = template.render(context_dict)
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("ISO-8859-1")), result)
    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    return None


def context_to_string(context):
    context_json = json.dumps(context)
    context_json_urlparse = urllib.parse.quote_plus(context_json)
    return context_json_urlparse


def string_to_context(string):
    context_json = urllib.parse.unquote_plus(string)
    context = json.loads(context_json)
    return context


def insert_newlines(string, every=64):
    return '\n'.join(string[i:i+every] for i in range(0, len(string), every))


def create_report_context(run, ss_sample, selected_stvs, report=None, user=None, commit=False):
    if ss_sample.sample.patient:
        patient = ss_sample.sample.patient.first_name + \
            ' ' + ss_sample.sample.patient.last_name
    else:
        patient = 'Not available'

    if commit:
        preview = None
    else:
        preview = 'static/placeholder1.pdf'

    context = {
        'preview': preview,
        'patient': patient,
        'sample_id': ss_sample.sample_identifier,
        'lab_no': ss_sample.sample.lab_no,
        'pipeline': run.pipeline_version.pipeline.name + ' (v.' + run.pipeline_version.version + ')',
        'worksheet': run.worksheet,
        'completion_date': run.completed_at.strftime("%Y-%m-%d"),
        'gene_key': ss_sample.gene_key
    }

    reported_by = None
    if report:
        context['title'] = report.name
        if report.pk:
            reported_by = report.get_user_created().get_full_name()
            report_creation_date = report.date_created.strftime(
                "%Y-%m-%d")
    else:
        context['title'] = 'report_' + \
            str(Report.objects.filter(
                run=run, samplesheetsample=ss_sample).count() + 1)

    if not reported_by:
        reported_by = user.get_full_name()
        report_creation_date = datetime.date.today().strftime("%Y-%m-%d")

    context['reported_by'] = reported_by
    context['report_creation_date'] = report_creation_date

    if report and report.summary:
        context['report_summary'] = report.summary
    else:
        context['report_summary'] = 'No summary provided'

    if report and report.recommendations:
        context['report_recommendations'] = report.recommendations
    else:
        context['report_recommendations'] = 'No recommendations provided'

    stvs = SampleTranscriptVariant.objects.filter(
        id__in=selected_stvs) \
        .annotate(num_comments=Count('comments')) \
        .order_by('-num_comments', '-comments__classification')

    stv_context = []
    stv_interpretations = []

    for index, stv in enumerate(stvs, start=1):
        comment = None
        if stv.comments.exists():
            classification = stv.comments.last().get_classification_display()
            classification_colour = stv.comments.last().classification_colour
            if stv.comments.last().comment:
                comment = stv.comments.last().comment
                stv_interpretations.append(
                    {'index': index, 'comment': comment})
        else:
            classification = 'Unclassified'
            classification_colour = 'blue'

        stv_dict = {'id': stv.id,
                    'gene': stv.transcript.gene.hgnc_name,
                    'transcript': stv.transcript.refseq_id,
                    'change': insert_newlines(stv.get_variant_list_title(), 30),
                    'classification': classification,
                    'classification_colour': classification_colour,
                    'comment': comment}

        stv_context.append(stv_dict)

    if stv_interpretations:
        context['interpretations'] = stv_interpretations
    else:
        context['no_interpretations'] = 'No interpretation provided'

    context['stvs'] = stv_context

    return context


def get_report_results(run, ss_sample, user, context=None):

    filters = get_filters(ss_sample.sample, run, user=user)
    filtered_variants = filter_variants(
        ss_sample.sample, run, filter=filters.get('active_filter'))

    results = []

    if context:
        current_pinned_stvs = filtered_variants['pinned'].values_list(
            'id', flat=True)
        stvs_in_report = [item.get('id') for item in context['stvs']]

        for reported_unpinned_stv in list(set(stvs_in_report)-set(current_pinned_stvs)):
            stv = SampleTranscriptVariant.objects.get(id=reported_unpinned_stv)

            comment = None
            if stv.comments.exists():
                classification = stv.comments.last().get_classification_display()
                classification_colour = stv.comments.last().classification_colour
                if stv.comments.last().comment:
                    comment = stv.comments.last().comment
            else:
                classification = 'Unclassified'
                classification_colour = 'blue'

            data = {'id': stv.id,
                    'display_name': stv.get_variant_list_title(),
                    'gene': stv.transcript.gene.hgnc_name,
                    'transcript': stv.transcript.refseq_id,
                    'classification': classification,
                    'classification_colour': classification_colour,
                    'comment': comment,
                    'selected': True,
                    'unpinned': True,
                    'updated': None, }

            results.append(data)

        for reported_pinned_stv in filtered_variants['pinned'].filter(id__in=stvs_in_report) \
            .annotate(num_comments=Count('comments')) \
                .order_by('-num_comments', '-comments__classification'):
            stv = reported_pinned_stv
            stv_report_version = next(
                (item for item in context['stvs'] if item["id"] == stv.id))

            updated = None
            comment = None
            previous_classification = None
            previous_classification_colour = None
            previous_comment = None
            if stv.comments.exists():
                classification = stv.comments.last().get_classification_display()
                classification_colour = stv.comments.last().classification_colour
                if stv_report_version.get('classification') != classification:
                    updated = 'classification'
                    previous_classification = stv_report_version.get(
                        'classification')
                    previous_classification_colour = stv_report_version.get(
                        'classification_colour')

                if stv.comments.last().comment:
                    comment = stv.comments.last().comment
                    if stv_report_version.get('comment') != comment:
                        if updated:
                            updated = 'both'
                        else:
                            updated = 'comment'
                        previous_comment = stv_report_version.get('comment')
            else:
                classification = 'Unclassified'
                classification_colour = 'blue'

            data = {'id': stv.id,
                    'display_name': stv.get_variant_list_title(),
                    'gene': stv.transcript.gene.hgnc_name,
                    'transcript': stv.transcript.refseq_id,
                    'classification': classification,
                    'classification_colour': classification_colour,
                    'previous_classification': previous_classification,
                    'previous_classification_colour': previous_classification_colour,
                    'comment': comment,
                    'previous_comment': previous_comment,
                    'selected': True,
                    'unpinned': False,
                    'updated': updated}

            results.append(data)

        for unreported_pinned_stv in filtered_variants['pinned'].exclude(id__in=stvs_in_report) \
            .annotate(num_comments=Count('comments')) \
                .order_by('-num_comments', '-comments__classification'):
            stv = unreported_pinned_stv

            comment = None
            if stv.comments.exists():
                classification = stv.comments.last().get_classification_display()
                classification_colour = stv.comments.last().classification_colour
                if stv.comments.last().comment:
                    comment = stv.comments.last().comment
            else:
                classification = 'Unclassified'
                classification_colour = 'blue'

            data = {'id': stv.id,
                    'display_name': stv.get_variant_list_title(),
                    'gene': stv.transcript.gene.hgnc_name,
                    'transcript': stv.transcript.refseq_id,
                    'classification': classification,
                    'classification_colour': classification_colour,
                    'comment': comment,
                    'selected': False,
                    'unpinned': False,
                    'updated': None}

            results.append(data)
    else:
        for stv in filtered_variants['pinned'] \
            .annotate(num_comments=Count('comments')) \
                .order_by('-num_comments', '-comments__classification'):
            comment = None
            selected = False
            if stv.comments.exists():
                classification = stv.comments.last().get_classification_display()
                classification_colour = stv.comments.last().classification_colour
                if classification != 'Unclassified':
                    selected = True
                if stv.comments.last().comment:
                    comment = stv.comments.last().comment
            else:
                classification = 'Unclassified'
                classification_colour = 'blue'

            data = {'id': stv.id,
                    'display_name': stv.get_variant_list_title(),
                    'gene': stv.transcript.gene.hgnc_name,
                    'transcript': stv.transcript.refseq_id,
                    'classification': classification,
                    'classification_colour': classification_colour,
                    'comment': comment,
                    'selected': selected,
                    'unpinned': False,
                    'updated': None}

            results.append(data)

    return {'stvs': results, 'excluded_pinned_variants_count': filtered_variants['excluded_pinned_variants_count']}


def update_selected_results(report_results, selected_stvs):
    for stv in report_results['stvs']:
        if stv['id'] in [int(i) for i in selected_stvs]:
            stv['selected'] = True
        else:
            stv['selected'] = False
    # report_results['stvs'] = sorted(
    #     report_results['stvs'], key=lambda k: k['selected'], reverse=True)

    return report_results


# from db.utils.filter_utils import filter_variants, get_filters
# run = Run.objects.get(worksheet='VmsG-127209')
# ss_sample = SamplesheetSample.objects.get(sample_identifier='sample-0024')
# report = Report.objects.last()
# user = User.objects.first()

# get_report_results(run,ss_sample,user,report)
