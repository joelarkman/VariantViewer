from db.models import SampleTranscriptVariant, VariantReport, VariantReportInfo
from web.models import Filter
import operator
from functools import reduce
from django.db.models import Q, Count, F, Func, IntegerField
from db.models import SampleTranscriptVariant
import urllib.parse
import json


def context_to_string(context):
    context_json = json.dumps(context)
    context_json_urlparse = urllib.parse.quote_plus(context_json)
    return context_json_urlparse


def string_to_context(string):
    context_json = urllib.parse.unquote_plus(string)
    context = json.loads(context_json)
    return context


def get_filters(sample, run, user):
    vcf = sample.vcfs.get(run=run)

    # Retrieve or create a blank filter template - to allow all filters to be removed.
    try:
        blank_filter = Filter.objects.annotate(
            c=Count('items')).get(description='7e5f04ff-1317-4224-a14e-f513bfdbc32f', c=0)
    except:
        blank_filter = Filter(
            name='none', description='7e5f04ff-1317-4224-a14e-f513bfdbc32f')
        blank_filter.save()

    # Try and locate a default filter associated with the relevent pipeline.
    try:
        pipeline_default_filter = Filter.objects.get(
            pipelineversion=run.pipeline_version)
    except:
        pipeline_default_filter = None

    # If some filters exist for the relevent vcf and user, retrieve them.
    if Filter.objects.filter(
            vcf=vcf, userfilter__user=user).exists():
        user_filters = Filter.objects.filter(
            vcf=vcf, userfilter__user=user)
    else:
        user_filters = None

    # Detect whether any of the filters associated with the user are selected.
    try:
        user_selected_filter = user_filters.get(
            vcf=vcf, userfilter__user=user, userfilter__selected=True)
        if user_selected_filter != blank_filter and not user_selected_filter.items.exists():
            user_selected_filter.delete()
            user_selected_filter = None
    except:
        user_selected_filter = None

    # If there is a user filter selected, set it to the active filter.
    if user_selected_filter:
        active_filter = user_selected_filter

    # Otherwise, if there is a pipeline default filter, set it to active.
    elif pipeline_default_filter:
        active_filter = pipeline_default_filter

    # Othwerwise do not define an active filter.
    else:
        active_filter = None

    # Ensure the list of filters associated with the user does not include the blank_filter.
    if user_filters:
        user_filters = user_filters.exclude(id=blank_filter.id)

    # if UserFilter.objects.filter(
    #         filter__vcf=vcf).exclude(filter__id=blank_filter.id).exclude(user__id=user.id).exists():
    #     other_user_filters = UserFilter.objects.filter(
    #         filter__vcf=vcf).exclude(filter__id=blank_filter.id).exclude(user__id=user.id)
    # else:
    #     other_user_filters = None

    return {'active_filter': active_filter,
            'pipeline_default_filter': pipeline_default_filter,
            'user_filters': user_filters,
            'blank_filter': blank_filter}


class ExtractValueInteger(Func):
    """ Returns the first int value from the string. Note that this
    requires the string to have an integer value inside.
    """
    function = 'REGEXP_MATCH'
    template = "CAST( (REGEXP_MATCH(value, '\d+'))[1] as INTEGER )"
    # If version of postgres is before v10 use below.
    # template = "CAST((SELECT REGEXP_MATCHES(value, '\d+')) as INTEGER)"
    output_field = IntegerField()


def filter_variants(sample, run, filter=None):

    # Load vcf associated with current sample + run
    vcf = sample.vcfs.get(run=run)

    if filter:
        # If filter has been provided...

        # Retrieve names of all fields of VariantReport model
        variantreport_fields = [
            f.name for f in VariantReport._meta.fields + VariantReport._meta.many_to_many]

        # Define blank containers.
        filters_list = []
        filter_cache = []

        # For each filter item, format field, filter_type and value information into a query dictionary containing relevent fk lookups.
        for item in filter.items.all().order_by('id'):
            if item.field in variantreport_fields:
                parsed_item = {
                    f'variant_report__{item.field}{item.filter_type}': item.value}
            elif item.field == 'impact':
                # This lookup finds variants with a particular impact value that have occured for this sample within a particular transcript.
                parsed_item = {f'variant_report__variant__samplevariant__sampletranscriptvariant__impact{item.filter_type}': item.value,
                               'variant_report__variant__samplevariant__sample__id': sample.id,
                               'variant_report__variant__samplevariant__sampletranscriptvariant__transcript__id': F('transcript')}
            elif item.field == 'consequence':
                # This lookup finds variants with a particular consequence value that have occured for this sample within a particular transcript.
                parsed_item = {f'variant_report__variant__samplevariant__sampletranscriptvariant__consequence{item.filter_type}': item.value,
                               'variant_report__variant__samplevariant__sample__id': sample.id,
                               'variant_report__variant__samplevariant__sampletranscriptvariant__transcript__id': F('transcript')}
            else:
                # If numerical info field use number_value instead of value.
                if item.filter_type in ['__lt', '__gt', '__lte', '__gte']:
                    parsed_item = {'tag': item.field,
                                   f'number_value{item.filter_type}': item.value}
                else:
                    parsed_item = {'tag': item.field,
                                   f'value{item.filter_type}': item.value}

            # Add latest item to cache list.
            filter_cache.append(parsed_item)

            # If current item does not mark the start or middle of an OR group, add filter cache to filter list and wipe it clean.
            if not item.or_next:
                filters_list.append(filter_cache)
                filter_cache = []

        # test = [
        #     {'variant_report__variant__samplevariant__sampletranscriptvariant__comments__classification': '1',
        #      'variant_report__variant__samplevariant__sample__id__ne': sample.id}]

        # test = [
        #     {'variant_report__variant__samplevariant__sampletranscriptvariant__comments__classification__isnull': False,
        #      'variant_report__variant__samplevariant__sampletranscriptvariant__comments__classification__ne': '0'}]

        # filters_list = [[
        #     {'variant_report__variant__samplevariant__sampletranscriptvariant__impact': 'HIGH',
        #      'variant_report__variant__samplevariant__sample__id': sample.id,
        #      'variant_report__variant__samplevariant__sampletranscriptvariant__transcript__id': F('transcript')}]]

        # filters_list.append(test)

        # Retrieve all STVs associated with current sample.
        STVs = SampleTranscriptVariant.objects.filter(
            sample_variant__sample=sample)

        transcript_key = 'variant_report__variant__samplevariant__sampletranscriptvariant__transcript__id'

        # Each item in filters_list contains a set of filers that should be OR'd together.
        for filter in filters_list:
            # Create a set of Q objects for each item in current OR group.
            k_v_pairs = (Q(**tag_value_pairs) for tag_value_pairs in filter)

            # If any filters are transcript specific
            if any(transcript_key in or_items for or_items in filter):
                # Retrieve all VRIs associated with current VCF file.
                # Use annotate to coerce 'field' value into an integer field.
                # Use annotate to append a transcript to each VRI, where a given variant appears in multiple
                # transcripts the rest of the VRI row will be duplicated.
                VRI_queryset = VariantReportInfo.objects.filter(
                    variant_report__vcf=vcf).annotate(number_value=ExtractValueInteger(), transcript=F(transcript_key))

                # Use reduce to place an OR between q objects and retrieve combinations of variant
                # and transcript IDs that satisfy current or group.
                variant_report_ids = VRI_queryset.filter(
                    reduce(operator.or_, k_v_pairs)).distinct().values_list(
                    'variant_report__variant', 'transcript')

                # Parse values_list output into list of filter dictionaries
                variants_transcripts = [
                    {'sample_variant__variant': value[0], 'transcript':value[1]} for value in variant_report_ids]

            else:
                # Retrieve all VRIs associated with current VCF file.
                # Use annotate to coerce 'field' value into an integer field.
                VRI_queryset = VariantReportInfo.objects.filter(
                    variant_report__vcf=vcf).annotate(number_value=ExtractValueInteger())

                # Use reduce to place an OR between q objects and retrieve combinations of variant
                # and transcript IDs that satisfy current or group.
                variant_report_ids = VRI_queryset.filter(
                    reduce(operator.or_, k_v_pairs)).distinct().values_list(
                    'variant_report__variant')

                # Parse values_list output into list of filter dictionaries
                variants_transcripts = [
                    {'sample_variant__variant': value[0]} for value in variant_report_ids]

            if variants_transcripts:
                # Create set of Q objects and use reduce to OR deliminate them and recursively filter STVs queryset
                # for objects with the correct variant transcript combinations.
                variants_transcripts = (Q(**v_t_pair)
                                        for v_t_pair in variants_transcripts)
                STVs = STVs.filter(
                    reduce(operator.or_, variants_transcripts)).distinct()
            else:
                STVs = STVs.none()

        # Apply ordering to STV list.
        STVs = STVs.order_by('transcript__gene__hgnc_name')

        # Retrieve the number of pinned variants for this sample/vcf regardless of filters.
        unfiltered_pinned_count = SampleTranscriptVariant.objects.filter(sample_variant__sample=sample,
                                                                         sample_variant__variant__variantreport__vcf=vcf,
                                                                         pinned=True).count()

        # Retrieve count of how many pinned variants have been excluded by the active filter.
        excluded_pinned_variants_count = unfiltered_pinned_count - \
            STVs.filter(pinned=True).count()
    else:
        # If no filter provided, return all variants.
        STVs = SampleTranscriptVariant.objects.filter(sample_variant__sample=sample,
                                                      sample_variant__variant__variantreport__vcf=vcf).order_by('transcript__gene__hgnc_name')

        excluded_pinned_variants_count = None

    # Return pinned and unpinned variants.
    return {'pinned': STVs.filter(pinned=True),
            'excluded_pinned_variants_count': excluded_pinned_variants_count,
            'unpinned': STVs.filter(selected=True, pinned=False),
            'variant_cache': context_to_string(list(STVs.values_list('id', flat=True)))}


def apply_variant_cache(sample, run, variant_cache):
    vcf = sample.vcfs.get(run=run)

    stv_ids = string_to_context(variant_cache)

    STVs = SampleTranscriptVariant.objects.filter(
        id__in=stv_ids).order_by('transcript__gene__hgnc_name')

    unfiltered_pinned_count = SampleTranscriptVariant.objects.filter(sample_variant__sample=sample,
                                                                     sample_variant__variant__variantreport__vcf=vcf,
                                                                     pinned=True).count()

    # Retrieve count of how many pinned variants have been excluded by the active filter.
    excluded_pinned_variants_count = unfiltered_pinned_count - \
        STVs.filter(pinned=True).count()

    return {'pinned': STVs.filter(pinned=True),
            'excluded_pinned_variants_count': excluded_pinned_variants_count,
            'unpinned': STVs.filter(selected=True, pinned=False)}
