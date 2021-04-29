from accounts.models import UserFilter
from db.models import SampleTranscriptVariant, VariantReport
from web.models import Filter
from django.db.models import Q, Count
from db.models import Sample, SampleTranscriptVariant


def get_filters(sample, run, user):
    vcf = sample.vcfs.get(run=run)

    try:
        blank_filter = Filter.objects.annotate(
            c=Count('items')).get(description='7e5f04ff-1317-4224-a14e-f513bfdbc32f', c=0)
    except:
        blank_filter = Filter(
            name='none', description='7e5f04ff-1317-4224-a14e-f513bfdbc32f')
        blank_filter.save()

    try:
        pipeline_default_filter = Filter.objects.get(
            pipelineversion=run.pipeline_version)
    except:
        pipeline_default_filter = None

    if Filter.objects.filter(
            vcf=vcf, userfilter__user=user).exists():
        user_filters = Filter.objects.filter(
            vcf=vcf, userfilter__user=user)
    else:
        user_filters = None

    try:
        user_selected_filter = user_filters.get(
            vcf=vcf, userfilter__user=user, userfilter__selected=True)
        if user_selected_filter != blank_filter and not user_selected_filter.items.exists():
            user_selected_filter.delete()
            user_selected_filter = None
    except:
        user_selected_filter = None

    if user_selected_filter:
        active_filter = user_selected_filter
    elif pipeline_default_filter:
        active_filter = pipeline_default_filter
    else:
        active_filter = None

    if user_filters:
        user_filters = user_filters.exclude(id=blank_filter.id)

    return {'active_filter': active_filter, 'pipeline_default_filter': pipeline_default_filter, 'user_filters': user_filters, 'blank_filter': blank_filter}


def filter_variants(sample, run, filter=None):
    vcf = sample.vcfs.get(run=run)

    if filter:
        # Retrieve names of all fields of VariantReport model
        variantreport_fields = [
            f.name for f in VariantReport._meta.fields + VariantReport._meta.many_to_many]

        # Iterate through Filter object. If field is in variantreport add to dictionary of filters that include field name
        # and filter type as the key and the provided value as the value.
        variant_report_filters = {
            f'{item.field}{item.filter_type}': item.value
            for item in filter.items.all() if item.field in variantreport_fields}

        # Iterate through Filter object. If field is not in variant report (it is instead a variant report info VRI tag) add to list of nested dictionaries.
        # Each dictionary in list contains a key,value pair for the VRI tag field and VRI value field. The key for value is appended with the provided filter type.
        variant_report_info_filters_list = [{'variantreportinfo__tag': item.field,
                                             f'variantreportinfo__value{item.filter_type}': item.value}
                                            for item in filter.items.all() if item.field not in variantreport_fields]

        # Create a set of Q objects for each dictionary in the variant_report_info_filters_list
        k_v_pairs = (Q(**tag_value_pairs)
                     for tag_value_pairs in variant_report_info_filters_list)

        # Set an initial queryset of all the variantreports associated with the vcf from the relevent sample & run.
        # Filter using the dictionary of variant_report_filters eg. quality and depth
        queryset = vcf.variantreport_set.filter(**variant_report_filters)

        # For loop functions in recursive fashion to chain the VRI filters together.
        # For each of the identified variant report info filters in k_v_pairs.
        for vri_filter in k_v_pairs:
            # Filter queryset using Q object (combination of VRI tag and Value)
            queryset = queryset.filter(vri_filter).distinct()

        # Extract the variant IDs that pass all variant report and variant report info filters.
        variant_ids = queryset.values_list('variant', flat=True)

        # Return set of STVs from the correct sample and where the variant has passed filters.
        # As the variant filtering starts with a VCF linked to a particular run, all STVs are also linked to the run.
        STVs = SampleTranscriptVariant.objects.filter(sample_variant__sample=sample,
                                                      sample_variant__variant__in=variant_ids).order_by('transcript__gene__hgnc_name')

        # Retrieve the number of pinned variants for this sample/vcf regardless of filters.
        unfiltered_pinned_count = SampleTranscriptVariant.objects.filter(sample_variant__sample=sample,
                                                                         sample_variant__variant__variantreport__vcf=vcf,
                                                                         pinned=True).count()

        # Retrieve count of how many pinned variants have been excluded by the active filter.
        excluded_pinned_variants_count = unfiltered_pinned_count - \
            STVs.filter(pinned=True).count()

    else:
        STVs = SampleTranscriptVariant.objects.filter(sample_variant__sample=sample,
                                                      sample_variant__variant__variantreport__vcf=vcf).order_by('transcript__gene__hgnc_name')

        excluded_pinned_variants_count = None

    return {'pinned': STVs.filter(pinned=True), 'excluded_pinned_variants_count': excluded_pinned_variants_count, 'unpinned': STVs.filter(selected=True, pinned=False)}
