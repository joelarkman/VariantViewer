from db.models import SampleTranscriptVariant
import urllib.parse
import json
from io import BytesIO
from django.http import HttpResponse
from django.template.loader import get_template

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


def create_report_context(run, ss_sample, included_stvs, report=None):
    if ss_sample.sample.patient.first_name:
        patient = ss_sample.sample.patient.first_name + \
            ' ' + ss_sample.sample.patient.last_name
    else:
        patient = 'Not available'

    context = {
        'title': report.name,
        'patient': patient,
        'sample_id': ss_sample.sample_identifier,
        'lab_no': ss_sample.sample.lab_no,
        'pipeline': run.pipeline_version.pipeline.name,
        'worksheet': run.worksheet,
        'completion_date': run.completed_at.strftime("%Y-%m-%d"),
        'gene_key': ss_sample.gene_key,
        'reported_by': report.get_user_created().get_full_name(),
        'report_creation_date': report.date_created.strftime("%Y-%m-%d")
    }

    if report.summary:
        context['report_summary'] = report.summary
    else:
        context['report_summary'] = 'No summary provided'

    if report.recommendations:
        context['report_recommendations'] = report.recommendations
    else:
        context['report_recommendations'] = 'No recommendations provided'

    stvs = SampleTranscriptVariant.objects.filter(
        id__in=included_stvs).order_by('comments__classification')

    stv_context = []
    stv_interpretations = []
    for stv in stvs:
        if stv.comments.exists():
            classification = stv.comments.last().get_classification_display()
            if stv.comments.last().comment:
                stv_interpretations.append(stv.comments.last().comment)
        else:
            classification = 'Unclassified'

        stv_dict = {'gene': stv.transcript.gene.hgnc_name,
                    'transcript': stv.transcript.refseq_id,
                    'hgvs_c': stv.get_short_hgvs()['hgvs_c'],
                    'hgvs_p': stv.get_short_hgvs()['hgvs_p'],
                    'classification': classification}

        stv_context.append(stv_dict)

    context['stvs'] = stv_context
    context['interpretations'] = stv_interpretations
    return context
