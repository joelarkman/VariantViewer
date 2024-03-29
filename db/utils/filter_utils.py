from django.db import connection
from accounts.models import UserFilter
from db.models import SampleTranscriptVariant, VariantReport, VariantReportInfo
from web.models import Filter
import operator
from functools import reduce
from django.db.models import Q, Count, F, Func, IntegerField
from db.models import Sample, SampleTranscriptVariant


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


# def filter_variants(sample, run, filter=None):
#     vcf = sample.vcfs.get(run=run)

#     if filter:
#         # Retrieve names of all fields of VariantReport model
#         variantreport_fields = [
#             f.name for f in VariantReport._meta.fields + VariantReport._meta.many_to_many]

#         # Iterate through Filter object. If field is in variantreport add to dictionary of filters that include field name
#         # and filter type as the key and the provided value as the value.
#         variant_report_filters = {
#             f'{item.field}{item.filter_type}': item.value
#             for item in filter.items.all() if item.field in variantreport_fields}

#         # Iterate through Filter object. If field is not in variant report (it is instead a variant report info VRI tag) add to list of nested dictionaries.
#         # Each dictionary in list contains a key,value pair for the VRI tag field and VRI value field. The key for value is appended with the provided filter type.
#         variant_report_info_filters_list = [{'variantreportinfo__tag': item.field,
#                                              f'variantreportinfo__value{item.filter_type}': item.value}
#                                             for item in filter.items.all() if item.field not in variantreport_fields]

#         # Create a set of Q objects for each dictionary in the variant_report_info_filters_list
#         k_v_pairs = (Q(**tag_value_pairs)
#                      for tag_value_pairs in variant_report_info_filters_list)

#         if filter.match == 'all':
#             # If filter set to match all of the provided filter items.....

#             print(variant_report_info_filters_list)

#             print(k_v_pairs)

#             # Filter set of variant reports associated with the relevent VCF using the dictionary
#             # of variant_report_filters eg. quality and depth
#             # This will chain them together e.g. seperate them with an &&.
#             queryset = vcf.variantreport_set.filter(**variant_report_filters)

#             # Iterate through VRI filters and chain them together.
#             for vri_filter in k_v_pairs:
#                 # Filter queryset using Q object (combination of VRI tag and Value)

#                 print(vri_filter)
#                 queryset = queryset.filter(vri_filter).distinct()

#         elif filter.match == 'any':
#             # If filter set to match any of the provided filter items.....

#             if variant_report_filters.items():
#                 # If there is at least one variant report field filter...
#                 # Seperate variant_report field filters into Q objects and insert an 'or' between them.
#                 list_of_Q = [Q(**{key: val})
#                              for key, val in variant_report_filters.items()]

#                 queryset = vcf.variantreport_set.filter(
#                     reduce(operator.or_, list_of_Q))
#             else:
#                 # Otherwise return all variant reports for this vcf.
#                 queryset = vcf.variantreport_set.all()

#             if variant_report_info_filters_list:
#                 # If there is at least one variant report info filter...
#                 # Combine the Q objects already created for VRIs and insert an 'or' between them.
#                 queryset = queryset.filter(
#                     reduce(operator.or_, k_v_pairs)).distinct()

#         # Extract the variant IDs that pass all variant report and variant report info filters.
#         variant_ids = queryset.values_list('variant', flat=True)

#         # Return set of STVs from the correct sample and where the variant has passed filters.
#         # As the variant filtering starts with a VCF linked to a particular run, all STVs are also linked to the run.
#         STVs = SampleTranscriptVariant.objects.filter(sample_variant__sample=sample,
#                                                       sample_variant__variant__in=variant_ids).order_by('transcript__gene__hgnc_name')

#         # Retrieve the number of pinned variants for this sample/vcf regardless of filters.
#         unfiltered_pinned_count = SampleTranscriptVariant.objects.filter(sample_variant__sample=sample,
#                                                                          sample_variant__variant__variantreport__vcf=vcf,
#                                                                          pinned=True).count()

#         # Retrieve count of how many pinned variants have been excluded by the active filter.
#         excluded_pinned_variants_count = unfiltered_pinned_count - \
#             STVs.filter(pinned=True).count()

#     else:
#         # If no filter provided, return all variants.
#         STVs = SampleTranscriptVariant.objects.filter(sample_variant__sample=sample,
#                                                       sample_variant__variant__variantreport__vcf=vcf).order_by('transcript__gene__hgnc_name')

#         excluded_pinned_variants_count = None

#     return {'pinned': STVs.filter(pinned=True), 'excluded_pinned_variants_count': excluded_pinned_variants_count, 'unpinned': STVs.filter(selected=True, pinned=False)}


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
    # initial = len(connection.queries)

    vcf = sample.vcfs.get(run=run)

    # print(len(connection.queries)-initial)

    if filter:
        # Retrieve names of all fields of VariantReport model
        variantreport_fields = [
            f.name for f in VariantReport._meta.fields + VariantReport._meta.many_to_many]

        variant_report_filters_list = []
        variant_report_info_filters_list = []
        for item in filter.items.all():
            if item.field in variantreport_fields:
                variant_report_filters_list.append(
                    {f'{item.field}{item.filter_type}': item.value})
            else:
                if item.filter_type in ['__lt', '__gt', '__lte', '__gte']:
                    variant_report_info_filters_list.append({'tag': item.field,
                                                             f'number_value{item.filter_type}': item.value})
                else:
                    variant_report_info_filters_list.append({'tag': item.field,
                                                             f'value{item.filter_type}': item.value})

        # print(len(connection.queries)-initial)

        filtered_VRs = []
        for filter_item in variant_report_filters_list:
            filtered_VRs.append(vcf.variantreport_set.filter(**filter_item).values_list(
                'id', flat=True))

        # Create an extra field that converts the 'value' field into an integer at the database level. This new field is saved as 'number_value'
        VRI_queryset = VariantReportInfo.objects.filter(
            variant_report__vcf=vcf).annotate(number_value=ExtractValueInteger())

        VRI_filtered_VRs = []
        for info_filter_item in variant_report_info_filters_list:
            VRI_filtered_VRs.append(VRI_queryset.filter(**info_filter_item).values_list(
                'variant_report', flat=True))

        if filter.match == 'all':
            if filtered_VRs:
                # Find the VRs that appear in all sub queries - match all filters.
                filtered_VRs_all = set(
                    filtered_VRs[0]).intersection(*filtered_VRs)

                queryset = vcf.variantreport_set.filter(
                    id__in=filtered_VRs_all)

                # print(len(connection.queries)-initial)

            else:
                queryset = vcf.variantreport_set.all()

            if VRI_filtered_VRs:
                # Find the VRs that appear in all sub queries - match all filters.
                VRI_filtered_VRs_all = set(
                    VRI_filtered_VRs[0]).intersection(*VRI_filtered_VRs)

                queryset = queryset.filter(id__in=VRI_filtered_VRs_all)

                # print(len(connection.queries)-initial)

            # print(len(connection.queries)-initial)

        elif filter.match == 'any':
            # If filter set to match any of the provided filter items.....
            if filtered_VRs:
                # Find the VRs that appear in any sub query - match any filter.
                filtered_VRs_any = set().union(*filtered_VRs)

                VR_queryset = vcf.variantreport_set.filter(
                    id__in=filtered_VRs_any)

            else:
                VR_queryset = vcf.variantreport_set.none()

            if VRI_filtered_VRs:
                # Find the VRs that appear in any sub query - match any filter.
                VRI_filtered_VRs_any = set().union(*VRI_filtered_VRs)

                VRI_queryset = vcf.variantreport_set.filter(
                    id__in=VRI_filtered_VRs_any)
            else:
                VRI_queryset = vcf.variantreport_set.none()

            # Find VRs that match any of VR or VRI filters.
            queryset = VR_queryset | VRI_queryset

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

        # print(len(connection.queries)-initial)

        # Retrieve count of how many pinned variants have been excluded by the active filter.
        excluded_pinned_variants_count = unfiltered_pinned_count - \
            STVs.filter(pinned=True).count()

    else:
        # If no filter provided, return all variants.
        STVs = SampleTranscriptVariant.objects.filter(sample_variant__sample=sample,
                                                      sample_variant__variant__variantreport__vcf=vcf).order_by('transcript__gene__hgnc_name')

        excluded_pinned_variants_count = None

    return {'pinned': STVs.filter(pinned=True), 'excluded_pinned_variants_count': excluded_pinned_variants_count, 'unpinned': STVs.filter(selected=True, pinned=False)}
