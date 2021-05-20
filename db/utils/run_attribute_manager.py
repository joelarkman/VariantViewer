import re
from typing import Type

from django.db.models import Model
from sample_sheet import SampleSheet as IlluminaSampleSheet
from typing import List
import vcf as py_vcf

from db.models import *
from db.utils.multiple_run_adder import MultipleRunAdder
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

    def get_related_instances(self, model_type: Type[Model], filters=None):
        """Fetch the run's nascent instance(s) of given model type"""
        many = None
        for update_model, update_many in MultipleRunAdder.update_order():
            if model_type == update_model:
                many=update_many
                break
        # cannot find the model type
        if many is None:
            raise ValueError(
                f"{model_type.__name__} is not defined in the update order."
            )

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

    def get_related_instance(self, *args, **kwargs):
        """As above but ensure unique"""
        related_instances = self.get_related_instances(*args, **kwargs)
        assert len(related_instances) == 1
        return related_instances[0]

    def get_all_instances(self, model_type) -> List[Model]:
        """Fetch all current instances of a given model type"""
        attribute_manager = self.run.attribute_managers[model_type]
        return attribute_manager.instances

    def get_pipeline(self) -> Pipeline:
        return Pipeline(
            name=self.run.pipeline
        )

    def get_pipeline_version(self) -> PipelineVersion:
        # TODO: add checks for updated/updates at the end of MCA
        return PipelineVersion(
            version=self.run.version,
            pipeline=self.get_related_instances(Pipeline),
        )

    def get_samplesheet(self) -> Samplesheet:
        # TODO: resolve latest_run issue
        return Samplesheet(
            path=self.run.samplesheet
        )

    def get_run(self) -> Run:
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

    def get_sample(self) -> List[Sample]:
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

    def get_samplesheet_sample(self) -> List[SamplesheetSample]:
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

    def get_bam(self) -> List[BAM]:
        bams = []
        for bam_file in self.run.bam_dir.glob('*.bam'):
            bam = BAM(
                path=str(bam_file.resolve()),
                run=self.get_related_instances(Run)
            )
            bams.append(bam)
        return bams

    def get_sample_bam(self) -> List[SampleBAM]:
        db_samples = self.get_related_instances(Sample)

        sample_bams = []
        for db_sample in db_samples:
            # loop through all actual bam files marked with sample lab no
            lab_no = db_sample.lab_no.replace('.', '-')
            for bam_file in self.run.bam_dir.glob(f'*{lab_no}*.bam'):
                f = {'path', str(bam_file.resolve())}
                # extract the nascent instance with the matching path
                db_bam = self.get_related_instances(BAM, filters=f)
                sample_bam = SampleBAM(
                    sample=db_sample,
                    bam=db_bam
                )
                sample_bams.append(sample_bam)
        return sample_bams

    def get_vcf(self) -> List[VCF]:
        variant_manager = self.run.multiple_run_adder.variant_manager

        vcfs = []
        for vcf_file in self.run.vcf_dir.glob('*unified*.vcf.gz'):
            vcf = VCF(
                path=str(vcf_file.resolve()),
                run=self.get_related_instances(Run)
            )
            vcfs.append(vcf)

            # keep track of all variants found in these VCFs for later addition
            reader = py_vcf.Reader(filename=vcf.path)
            if not variant_manager.csq_keys:
                # add variant record headers to the manager if not present
                keys = reader.infos['CSQ'].desc.split('Format: ')[-1].split('|')
                variant_manager.csq_keys = keys
            for record in reader:
                variant_manager.records.append(record)
        return vcfs

    def get_sample_vcf(self) -> List[SampleVCF]:
        db_samples = self.get_related_instances(Sample)
        sample_vcfs = []
        for db_sample in db_samples:
            lab_no = db_sample.lab_no.replace('.', '-')
            for vcf_file in self.run.vcf_dir.glob(f'*{lab_no}*.vcf.gz'):
                f = {'path', str(vcf_file.resolve())}
                db_vcf = self.get_related_instances(VCF, filters=f)
                sample_vcf = SampleVCF(
                    sample=db_sample,
                    vcf=db_vcf
                )
                sample_vcfs.append(sample_vcf)
        return sample_vcfs

    def get_excel_report(self) -> List[ExcelReport]:
        excel_reports = []
        db_samples = self.get_related_instances(Sample)
        for db_sample in db_samples:
            lab_no = db_sample.lab_no.replace('.', '-')
            for excel_file in self.run.excel_dir.glob(f'*{lab_no}*.xlsx'):
                excel_report = ExcelReport(
                    path=str(excel_file.resolve()),
                    run=self.get_related_instances(Run),
                    sample=db_sample,
                )
                excel_reports.append(excel_report)
        return excel_reports

    def get_gene(self) -> List[Gene]:
        genes = []
        variant_manager = self.run.multiple_run_adder.variant_manager
        gene_df = variant_manager.df[["SYMBOL", "Gene"]].drop_duplicates()
        for index, row in gene_df.iterrows():
            if row.SYMBOL:
                gene = Gene(
                    hgnc_name=row.SYMBOL,
                    hgnc_id=row.Gene
                )
                genes.append(gene)
        return genes

    def get_transcript(self) -> List[Transcript]:
        transcripts = []
        variant_manager = self.run.multiple_run_adder.variant_manager
        transcript_df = variant_manager.df[
            ["Gene", "Feature_type", "Feature", "CANONICAL"]
        ]
        transcript_df = transcript_df.drop_duplicates()
        for index, row in transcript_df.iterrows():
            if row.Feature_type == "Transcript":
                gene = self.get_related_instances(Gene, {'hgnc_id': row.Gene})
                transcript = Transcript(
                    gene=gene,
                    refseq_id=row.Feature,
                    name=row.Feature,
                    canonical=row.CANONICAL == "YES"
                )
                transcripts.append(transcript)
        return transcripts

    def get_exon(self) -> List[Exon]:
        exons = []
        variant_manager = self.run.multiple_run_adder.variant_manager
        transcript_df = variant_manager.df[
            ["Gene", "Feature_type", "Feature", "CANONICAL", "EXON"]
        ]
        exon_df = transcript_df.drop_duplicates(subset=["Gene","Feature"])
        for index, row in exon_df.iterrows():
            if not row.Gene or row.Feature_type != "Transcript" or not row.EXON:
                continue
            f = {'refseq_id': row.Feature}
            db_transcript = self.get_related_instances(Transcript, f)
            for i in range(row.EXON.split('/')[-1]):
                exon = Exon(
                    number=i+1,
                    transcript=db_transcript,
                )
                exons.append(exon)
        return exons

    def get_variant(self) -> List[Variant]:
        variants = []
        # create the models using vcf records added when VCFs had been added
        for record in self.run.multiple_run_adder.variant_manager.records:
            variant = Variant(
                ref=record.REF,
                alt=record.ALT
            )
            variants.append(variant)
        return variants

    def get_sample_variant(self) -> List[SampleVariant]:
        sample_variants = []
        # look through all the variant reports in the variant manager
        for record in self.run.multiple_run_adder.variant_manager.records:
            # fetch the matching variant and sample from db
            f = {'ref': record.ref, 'alt': record.alt}
            db_variant: Variant = self.get_related_instance(Variant, filters=f)
            sample = record.samples[0]
            lab_no_re = r'D(\d{2})-(\d{5})'

            # noinspection PyTypeChecker
            lab_no = '.'.join(re.match(lab_no_re, sample.sample).groups([1,2]))
            f = {'lab_no': lab_no}
            db_sample: Sample = self.get_related_instance(Sample, filters=f)
            sample_variant = SampleVariant(
                sample=db_sample,
                variant=db_variant
            )
            sample_variants.append(sample_variant)
        return sample_variants

    def get_transcript_variant(self) -> List[TranscriptVariant]:
        transcript_variants = []
        db_txs: List[Transcript] = self.get_related_instances(Transcript)
        db_variants: List[Variant] = self.get_related_instances(Variant)
        variants_df = self.run.multiple_run_adder.variant_manager.df

        for db_tx in db_txs:
            transcript_variants_df = variants_df[
                (variants_df.Feature == db_tx.refseq_id)
            ]
        return transcript_variants

    def get_sample_transcript_variant(self):
        pass

    def get_genome_build(self):
        pass

    def get_genomic_coordinate(self):
        pass

    def get_variant_coordinate(self):
        pass

    def get_sequence(self):
        pass

    def get_exon_sequence(self):
        pass

    def get_coverage_info(self):
        pass

    def get_exon_report(self):
        pass

    def get_gene_report(self):
        pass

    def get_variant_report(self):
        pass

    def get_variant_report_info(self):
        pass