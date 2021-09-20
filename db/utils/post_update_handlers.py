def post_update_handlers(model_type, objects):
    if hasattr(model_type, 'post_save_method') and callable(model_type.post_save_method):
        for object in objects:
            model_type.post_save_method(object)


for run in Run.objects.all():
    run.samplesheet.latest_run = Run.objects.filter(
        samplesheet=run.samplesheet).order_by('-completed_at')[0]
    run.samplesheet.save()

for sample in Sample.objects.all():
    Sample.SetSampleSection(sample)


for vcf in VCF.objects.all():
    VCF.create_symlink(vcf)

for bam in BAM.objects.all():
    BAM.create_symlink(bam)
