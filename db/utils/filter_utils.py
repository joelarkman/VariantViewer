from db.models import SampleTranscriptVariant, VariantReport
from web.models import Filter
from django.db.models import Q
from db.models import Sample, SampleTranscriptVariant


def get_filter(sample, run, user=None):
    vcf = sample.vcfs.get(run=run)

    return Filter.objects.filter(vcf=vcf).last()


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
    else:
        STVs = SampleTranscriptVariant.objects.filter(sample_variant__sample=sample,
                                                      sample_variant__variant__variantreport__vcf=vcf).order_by('transcript__gene__hgnc_name')

    return {'pinned_variants': STVs.filter(pinned=True), 'unpinned_variants': STVs.filter(selected=True, pinned=False)}
