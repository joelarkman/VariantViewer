from db.utils.run_model import RunModel
from db.utils.run_model import ManyRunModel


class RunAttributeManager:
    def __init__(self, run, model_type, objects, many=False):
        """
        Args:
            run (object): the run for which this object holds data
            model_type:  the db table to which the held data corresponds
            objects: pre-existing db records for this model_type
        """
        self.run = run
        self.model_type = model_type
        self.objects = objects
        self.many=many

        # access delegate function & class for parsing correct data types
        model_str = model_type._meta.verbose_name.replace(' ', '_')
        get_model_attrs = getattr(self, model_str)
        if many:
            run_model = ManyRunModel(model_type, get_model_attrs(), objects)
        else:
            run_model = RunModel(model_type, get_model_attrs(), objects)
        self.run_model = run_model

    def get_pipeline(self):
        pass

    def get_pipeline_version(self):
        pass

    def get_run(self):
        pass

    def get_samplesheet(self):
        pass

    def get_patient(self):
        pass

    def get_sample(self):
        pass

    def get_samplesheet_sample(self):
        pass

    def get_bam(self):
        pass

    def get_sample_bam(self):
        pass

    def get_vcf(self):
        pass

    def get_sample_vcf(self):
        pass

    def get_variant(self):
        pass

    def get_sample_variant(self):
        pass

    def get_gene(self):
        pass

    def get_transcript(self):
        pass

    def get_exon(self):
        pass

    def get_coverage_info(self):
        pass

    def get_exon_report(self):
        pass

    def get_gene_report(self):
        pass

    def get_genome_build(self):
        pass

    def get_genomic_coordinate(self):
        pass

    def get_sequence(self):
        pass

    def get_exon_sequence(self):
        pass

    def get_variant_coordinate(self):
        pass

    def get_transcript_variant(self):
        pass

    def get_sample_transcript_variant(self):
        pass

    def get_variant_report(self):
        pass

    def get_variant_report_info(self):
        pass