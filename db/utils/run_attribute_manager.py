import re

from sample_sheet import SampleSheet as IlluminaSampleSheet

from db.models import *
from db.utils.run_builder import RunBuilder
from db.utils.run_model import RunModel
from db.utils.run_model import ManyRunModel


class RunAttributeManager:
    def __init__(self, run: RunBuilder, model_type, instances, many=False):
        """
        Args:
            run (object): the RunBuilder for which this object holds data
            model_type:  the db table to which the held data corresponds
            instances: pre-existing db records for this model_type
        """
        self.run = run
        self.model_type = model_type
        self.instances = instances
        self.many=many
        # noinspection PyProtectedMember
        model_str = model_type._meta.verbose_name.replace(' ', '_')

        # create a delegate function for parsing the correct data for type
        get_model_attrs = getattr(self, model_str)

        # create a dictionary of data values from the model
        # model used purely for field validation, we need a dict for later
        if not many:
            model_attrs = get_model_attrs().__dict__
            # model instances have a dict value '_state', remove to instantiate
            model_attrs.pop('_state')
            run_model = RunModel(model_type, model_attrs, instances)
        else:
            model_attrs_list = [model.__dict__ for model in get_model_attrs()]
            map(lambda x: x.pop('_state'), model_attrs_list)
            run_model = ManyRunModel(model_type, model_attrs_list, instances)

        self.run_model = run_model

    def get_related_instances(self, model_type, many=False, filters=None):
        """Fetch the run's nascent instance(s) of given model type"""

        if filters is None:
            filters = {}
        attribute_manager = self.run.attribute_managers[model_type]
        if not many:
            return attribute_manager.run_model.entry
        else:
            entry_list = attribute_manager.run_model.entry_list()
            if not filters:
                return entry_list
            filtered_entries = entry_list

            for attr, value in filters.items():
                # loop through desired filters to progressively filter entries
                filtered_entries = [
                    entry for entry in filtered_entries
                    if getattr(entry, attr) == value
                ]
            return filtered_entries

    def get_all_instances(self, model_type):
        """Fetch all current instances of a given model type"""
        attribute_manager = self.run.attribute_managers[model_type]
        return attribute_manager.instances

    def get_pipeline(self):
        return Pipeline(
            name=self.run.pipeline
        )

    def get_pipeline_version(self):
        # TODO: add checks for updated/updates at the end of MCA
        return PipelineVersion(
            version=self.run.version,
            pipeline=self.get_related_instances(Pipeline),
        )

    def get_samplesheet(self):
        # TODO: resolve latest_run issue
        return Samplesheet(
            path=self.run.samplesheet
        )

    def get_run(self):
        """Fetch info to populate a Run model instance"""
        return Run(
            worksheet=self.run.worksheet,
            command_line_usage=self.run.commandline_usage,
            completed_at=self.run.completed_at,
            output_dir=self.run.output_dir,
            fastq_dir=self.run.fastq_dir,
            interop_dir=self.run.interop_dir,
            pipeline_version=self.get_related_instances(PipelineVersion)
        )


    def get_sample(self):
        """Fetch info to populate a Sample model instance

        Since there are many samples per run, we must return a list
        """
        samplesheet_file = self.run.samplesheet
        samplesheet = IlluminaSampleSheet(samplesheet_file)

        # compile a regex search string for lab number
        lab_no_pattern = re.compile(r'D\d{2}\.\d{5}')

        samples = []
        for sample in samplesheet.samples:
            # ignore negative controls
            sample_name = sample.Sample_Name
            if "Neg" in sample_name: continue
            lab_no = lab_no_pattern.search(sample_name)
            samples.append(
                Sample(
                    lab_no=lab_no,
                    slug=slugify(lab_no)
                )
            )

        return samples

    def get_samplesheet_sample(self):
        db_samplesheet = self.get_related_instances(Samplesheet)
        db_samples = self.get_related_instances(Sample)

        samplesheet = IlluminaSampleSheet(self.run.samplesheet)
        samples = samplesheet.samples

        samplesheet_samples = []
        for db_sample in db_samples:
            sample = [sample for sample in samples
                      if db_sample.lab_no in sample.Sample_Name][0]
            samplesheet_samples.append(
                SamplesheetSample(
                    samplesheet=db_samplesheet,
                    sample=db_sample,
                    sample_identifier=sample.Sample_ID,
                    index=sample.index,
                    # values not present will return None using OOP-based access
                    index2=sample.index2,
                    gene_key=sample.Sample_Project
                )
            )
        return samplesheet_samples

    def get_bam(self):
        bams = []
        for bam_file in self.run.bam_dir.glob('*.bam'):
            bam = BAM(
                path=bam_file.absolute(),
                run=self.get_related_instances(Run)
            )
            bams.append(bam)
        return bams

    def get_sample_bam(self):
        db_samples = self.get_related_instances(Sample, many=True)

        sample_bams = []
        for db_sample in db_samples:
            # loop through all actual bam files marked with sample lab no
            for bam_file in self.run.bam_dir.glob(f'*{db_sample.lab_no}*.bam'):
                f = {'path', bam_file.absolute()}
                # extract the nascent instance with the matching path
                db_bam = self.get_related_instances(BAM, many=True, filters=f)
                sample_bam = SampleBAM(
                    sample=db_sample,
                    bam=db_bam
                )
                sample_bams.append(sample_bam)
        return sample_bams


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