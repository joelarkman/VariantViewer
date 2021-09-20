import os
import re
import tempfile
from typing import Any
from typing import Dict
from typing import List
from typing import Type

import pandas as pd
from django.db.models import Model
from openpyxl import load_workbook
from sample_sheet import SampleSheet as IlluminaSampleSheet

from VariantViewer.utils.notebook import is_notebook

if is_notebook():
    from tqdm.notebook import tqdm
else:
    from tqdm import tqdm

from db.models import *
from db.utils.run_builder import RunBuilder
from db.utils.run_model import RunModel
from db.utils.run_model import ManyRunModel

LABNO_PATTERN = re.compile(r'([Dd]\d{2}[.-]\d{5})')


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
        self.many = many
        self.lookup_index = {}
        # noinspection PyProtectedMember
        model_str = model_type._meta.verbose_name.replace(' ', '_')

        # create a delegate function for parsing the correct data for type
        # this essentially acts like a case switch, in which the particular
        # RunAttributeManager object will only ever have 1 state.
        get_model_attrs = getattr(self, f"get_{model_str}")

        # create a dictionary of data values from the model
        # model used purely for field validation, we need a dict for later
        if not many:
            model_attrs = get_model_attrs()
            run_model = RunModel(model_type, model_attrs, instances)
        else:
            model_attrs_lst = [model_attrs for model_attrs in get_model_attrs()]
            run_model = ManyRunModel(model_type, model_attrs_lst, instances)

        self.run_model = run_model

    def related_instances(self, model_type: Type[Model], filters=None):
        """Fetch the run's nascent instance(s) of given model type"""
        # TODO: fix issue where returning false for pipeline
        many = None
        update_order = self.run.multiple_run_adder.update_order()
        for update_model, update_many in update_order:
            if model_type == update_model:
                many = update_many
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
            # just one will be present, return as list to ensure 1
            return [attribute_manager.run_model.entry]

        else:
            entry_list = attribute_manager.run_model.entry_list()
            if not filters:
                # no filters given, return all related items
                return entry_list

        # apply filters
        filtered = entry_list

        if len(filters.items()) == 1:
            # attempt to use the MRA lookup index to speed process up
            attr, value = list(filters.items())[0]

            # get or set the item based on the filter

            item_key = f"{attr}_{value}"
            item_lookup = self.lookup_index.get(item_key)
            if not item_lookup:
                objs = [x for x in filtered if getattr(x, attr) == value]
                self.lookup_index[item_key] = objs
                item_lookup = self.lookup_index[item_key]
            return item_lookup

        for attr, value in filters.items():
            # loop through desired filters to progressively filter entries
            filtered = [
                entry for entry in filtered
                if getattr(entry, attr) == value
            ]
        return filtered

    def related_instance(self, *args, **kwargs):
        """As above but ensure unique"""
        related_instances = self.related_instances(*args, **kwargs)
        assert len(related_instances) == 1, \
            f"error finding {self.model_type}: " \
            f"{related_instances} (" \
            f"{kwargs['filters']})"
        return related_instances[0]

    def get_all_instances(self, model_type) -> List[Model]:
        """Fetch all current instances of a given model type"""
        attribute_manager = self.run.attribute_managers[model_type]
        return attribute_manager.instances

    def get_pipeline(self) -> Dict[str, Any]:
        pipeline_attrs = {'name': self.run.pipeline}
        return pipeline_attrs

    def get_pipeline_version(self) -> Dict[str, Any]:
        # TODO: add checks for updated/updates at the end of MCA
        pipeline_version_attrs = {
            'version': self.run.version,
            'pipeline': self.related_instance(Pipeline)
        }
        return pipeline_version_attrs

    def get_samplesheet(self) -> Dict[str, Any]:
        # TODO: resolve latest_run issue
        samplesheet_attrs = {'path': self.run.samplesheet}
        return samplesheet_attrs

    def get_run(self) -> Dict[str, Any]:
        """Fetch info to populate a Run model instance"""
        run_attrs = {
            'worksheet': self.run.worksheet,
            'command_line_usage': '\n'.join(self.run.commandline_usage),
            'samplesheet': self.related_instance(Samplesheet),
            'completed_at': self.run.completed_at,
            'config_file': self.run.config_file,
            'output_dir': self.run.output_dir,
            'fastq_dir': self.run.fastq_dir,
            'interop_dir': self.run.interop_dir,
            'pipeline_version': self.related_instance(PipelineVersion)
        }
        return run_attrs

    def get_sample(self) -> List[Dict[str, Any]]:
        """Fetch info to populate a Sample model instance

        Since there are many samples per run, we must return a list
        """
        samples: List[Dict[str, Any]] = []

        samplesheet_file = self.run.samplesheet

        ss_temp = tempfile.NamedTemporaryFile(delete=False)
        # fix empty header values
        with open(self.run.samplesheet, 'rt') as f_in:
            with open(ss_temp.name, 'wt') as f_out:
                for line in f_in:
                    f_out.write(line.replace('Reason,', 'Reason'))

        samplesheet = IlluminaSampleSheet(ss_temp.name)
        samplesheet_samples = tqdm(samplesheet.samples, leave=False)
        for sample in samplesheet_samples:
            # ignore negative controls
            sample_name = sample.Sample_Name
            if "Neg" in sample_name: continue
            lab_no = LABNO_PATTERN.search(sample_name).group().replace('-', '.')
            samples.append({
                'lab_no': lab_no,
            })
        samplesheet_samples.close()
        os.remove(ss_temp.name)
        return samples

    def get_samplesheet_sample(self) -> List[Dict[str, Any]]:
        samplesheet_samples: List[Dict[str, Any]] = []

        db_samplesheet = self.related_instance(Samplesheet)
        db_samples = self.related_instances(Sample)
        ss_temp = tempfile.NamedTemporaryFile(delete=False)

        # fix empty header values
        with open(self.run.samplesheet, 'rt') as f_in:
            with open(ss_temp.name, 'wt') as f_out:
                for line in f_in:
                    f_out.write(line.replace('Reason,', 'Reason'))

        samplesheet = IlluminaSampleSheet(ss_temp.name)
        samples = samplesheet.samples

        db_samples = tqdm(db_samples, leave=False)
        for db_sample in db_samples:
            # check through the samplesheet again for the sample added to db
            sample = None
            for ss_sample in samples:
                labno = ss_sample.Sample_Name
                labno = LABNO_PATTERN.search(labno).group().replace('-', '.')
                if labno == db_sample.lab_no:
                    sample = ss_sample
                    break
            if not Sample:
                raise ValueError(f"{db_sample} not found in {db_samplesheet}")
            samplesheet_samples.append({
                "samplesheet": db_samplesheet,
                "sample": db_sample,
                "sample_identifier": sample.Sample_ID,
                "index": sample.index,
                # values not present will return None using OOP-based access
                "index2": sample.index2,
                "gene_key": sample.Sample_Project
            })
        db_samples.close()
        os.remove(ss_temp.name)
        return samplesheet_samples

    def get_bam(self) -> List[Dict[str, Any]]:
        bams = []
        bam_files = tqdm(list(self.run.bam_dir.glob('*.bam')), leave=False)
        for bam_file in bam_files:
            bams.append({
                "path": str(bam_file.resolve()),
                "run": self.related_instance(Run)
            })
        bam_files.close()
        return bams

    def get_sample_bam(self) -> List[Dict[str, Any]]:
        db_samples = tqdm(self.related_instances(Sample), leave=False)

        sample_bams = []
        for db_sample in db_samples:
            # loop through all actual bam files marked with sample lab no
            lab_no = db_sample.lab_no.replace('.', '-')
            for bam_file in self.run.bam_dir.glob(f'*{lab_no}*.bam'):
                f = {'path': str(bam_file.resolve())}
                # extract the nascent instance with the matching path
                db_bam = self.related_instance(BAM, filters=f)
                sample_bams.append({
                    "sample": db_sample,
                    "bam": db_bam
                })
        db_samples.close()
        return sample_bams

    def get_vcf(self) -> List[Dict[str, Any]]:
        variant_manager = self.run.multiple_run_adder.variant_manager

        vcfs = []
        vcf_filenames = []
        vcf_files = tqdm(
            list(self.run.vcf_dir.glob('*unified*.vcf.gz')),
            leave=False
        )
        for vcf_file in vcf_files:
            vcf_filename = str(vcf_file.resolve())
            vcfs.append({
                "path": vcf_filename,
                "run": self.related_instance(Run)
            })
            vcf_filenames.append(vcf_filename)
            # keep track of all variants found in these VCFs for later addition
            variant_manager.update_records(vcf_filename)
        vcf_files.close()
        return vcfs

    def get_sample_vcf(self) -> List[Dict[str, Any]]:
        db_samples = tqdm(self.related_instances(Sample), leave=False)
        sample_vcfs = []
        for db_sample in db_samples:
            lab_no = db_sample.lab_no.replace('.', '-')
            for vcf_file in self.run.vcf_dir.glob(f'*{lab_no}*.vcf.gz'):
                f = {'path': str(vcf_file.resolve())}
                db_vcf = self.related_instance(VCF, filters=f)
                sample_vcfs.append({
                    "sample": db_sample,
                    "vcf": db_vcf
                })
        db_samples.close()
        return sample_vcfs

    def get_excel_report(self) -> List[Dict[str, Any]]:
        excel_reports = []
        db_samples = tqdm(self.related_instances(Sample), leave=False)
        for db_sample in db_samples:
            lab_no = db_sample.lab_no.replace('.', '-')
            excel_files = self.run.excel_dir.glob(f'*{lab_no}*results.xlsx')
            for excel_file in tqdm(excel_files, leave=False):
                # skip recovery files
                if excel_file.name[0] == '~': continue
                excel_report = {
                    "path": str(excel_file.resolve()),
                    "run": self.related_instance(Run),
                    "sample": db_sample,
                }
                excel_reports.append(excel_report)
        db_samples.close()
        return excel_reports

    def get_genome_build(self) -> List[Dict[str, Any]]:
        genome_builds = []
        variant_manager = self.run.multiple_run_adder.variant_manager
        variant_df = variant_manager.variant_df
        for build in variant_df.build.unique():
            genome_build = {
                'name': build
            }
            genome_builds.append(genome_build)
        return genome_builds

    def get_gene(self) -> List[Dict[str, Any]]:
        genes = []
        variant_manager = self.run.multiple_run_adder.variant_manager
        gene_df = variant_manager.gene_df
        gene_rows = tqdm(list(gene_df.iterrows()), leave=False)
        for index, row in gene_rows:
            gene = {
                "hgnc_name": row.SYMBOL,
                "hgnc_id": row.Gene
            }
            genes.append(gene)
        gene_rows.close()
        return genes

    def get_transcript(self) -> List[Dict[str, Any]]:
        # TODO: include RegulatoryFeature, MotifFeature
        transcripts = []
        variant_manager = self.run.multiple_run_adder.variant_manager
        transcript_df = variant_manager.transcript_df

        transcript_rows = tqdm(list(transcript_df.iterrows()), leave=False)
        for index, row in transcript_rows:
            if row.Feature_type == "Transcript":
                gene = self.related_instance(
                    Gene,
                    filters={'hgnc_id': str(row.Gene)}
                )
                transcript = {
                    "gene": gene,
                    "refseq_id": row.Feature,
                    "name": row.Feature,
                    "canonical": row.CANONICAL
                }
                transcripts.append(transcript)
        return transcripts

    def get_exon(self) -> List[Dict[str, Any]]:
        # TODO: include intron
        exons = []
        variant_manager = self.run.multiple_run_adder.variant_manager
        transcript_df = variant_manager.transcript_df
        transcript_rows = tqdm(list(transcript_df.iterrows()), leave=False)
        for index, row in transcript_rows:
            if not row.EXON:
                continue
            tx_f = {'refseq_id': row.Feature}
            b_f = {'name': row.build}
            db_transcript = self.related_instance(Transcript, tx_f)
            db_genome_build = self.related_instance(GenomeBuild, b_f)
            for i in range(row.EXON + 1):
                exon = {
                    # ensure 0 is created too
                    "number": i,
                    "transcript": db_transcript,
                    "genome_build": db_genome_build
                }
                exons.append(exon)
        transcript_rows.close()
        return exons

    def get_variant(self) -> List[Dict[str, Any]]:
        variants = []
        # create the models using vcf records added when VCFs had been added
        variant_manager = self.run.multiple_run_adder.variant_manager
        variant_df = variant_manager.variant_df.drop_duplicates(
            subset=['CHROM', 'POS', 'REF', 'ALT', 'build']
        )

        variant_rows = tqdm(list(variant_df.iterrows()), leave=False)
        for index, row in variant_rows:
            # fetch the genome build
            b_f = {'name': row.build}
            db_genome_build = self.related_instance(GenomeBuild, b_f)

            variant = {
                "chrom": row.CHROM,
                "pos": row.POS,
                "ref": row.REF,
                "alt": row.ALT,
                "genome_build": db_genome_build
            }
            variants.append(variant)
        variant_rows.close()
        return variants

    def get_sample_variant(self) -> List[Dict[str, Any]]:
        sample_variants = []
        db_samples = self.related_instances(Sample)
        sample_labnos = [db_sample.lab_no for db_sample in db_samples]

        variant_manager = self.run.multiple_run_adder.variant_manager
        variant_df = variant_manager.variant_df.drop_duplicates(
            subset=["Sample", "CHROM", "POS", "REF", "ALT", "build"]
        )
        worksheet_variant_df = variant_df[variant_df.Sample.isin(sample_labnos)]
        variant_rows = tqdm(list(worksheet_variant_df.iterrows()), leave=False)
        for index, row in variant_rows:
            sample_f = {"lab_no": row.Sample}
            variant_f = {
                "chrom": row.CHROM,
                "pos":   row.POS,
                "ref":   row.REF,
                "alt":   row.ALT
            }
            sample_variant = {
                "sample": self.related_instance(Sample, filters=sample_f),
                "variant": self.related_instance(Variant, filters=variant_f)
            }
            sample_variants.append(sample_variant)
        variant_rows.close()
        return sample_variants

    def get_transcript_variant(self) -> List[Dict[str, Any]]:
        transcript_variants = []
        variant_manager = self.run.multiple_run_adder.variant_manager
        transcript_variant_df = variant_manager.transcript_variant_df
        df_rows = tqdm(list(transcript_variant_df.iterrows()), leave=False)
        for index, row in df_rows:
            tx_f = {"refseq_id": row.Feature}
            variant_f = {
                "chrom": row.CHROM,
                "pos": row.POS,
                "ref": row.REF,
                "alt": row.ALT
            }
            db_variant = self.related_instance(Variant, filters=variant_f)
            db_transcript = self.related_instance(Transcript, filters=tx_f)
            transcript_variant = {
                'transcript': db_transcript,
                'variant': db_variant,
                'hgvs_c': row.HGVSc,
                'hgvs_p': row.HGVSp
            }
            transcript_variants.append(transcript_variant)
        df_rows.close()

        return transcript_variants

    def get_sample_transcript_variant(self) -> List[Dict[str, Any]]:
        # TODO: remember to talk about setting selected
        sample_transcript_variants = []
        variant_manager = self.run.multiple_run_adder.variant_manager
        tv_df = variant_manager.sample_transcript_variant_df
        lab_nos = list(map(lambda x: x.lab_no, self.related_instances(Sample)))
        stv_df = tv_df[tv_df.Sample.isin(lab_nos)]

        df_rows = tqdm(list(stv_df.iterrows()), leave=False)

        for index, row in df_rows:
            tx_f = {"refseq_id": row.Feature}
            sample_f = {"lab_no": row.Sample}
            variant_f = {
                "chrom": row.CHROM,
                "pos": row.POS,
                "ref": row.REF,
                "alt": row.ALT
            }
            db_transcript = self.related_instance(Transcript, filters=tx_f)
            db_sample = self.related_instance(Sample, filters=sample_f)
            db_variant = self.related_instance(Variant, filters=variant_f)

            sv_f = {"sample_id": db_sample.id, "variant_id": db_variant.id}
            df_sv = self.related_instance(SampleVariant, filters=sv_f)
            sample_transcript_variant = {
                "transcript": db_transcript,
                "sample_variant": df_sv,
                "selected": row.CANONICAL,
                "consequence": row.Consequence,
                "impact": row.IMPACT
            }
            sample_transcript_variants.append(sample_transcript_variant)
        return sample_transcript_variants

    def get_variant_report(self) -> List[Dict[str, Any]]:
        variant_reports = []
        variant_manager = self.run.multiple_run_adder.variant_manager
        variant_df = variant_manager.variant_df.drop_duplicates(
            subset=["Sample", "CHROM", "POS", "REF", "ALT", "build"]
        )
        lab_nos = list(map(lambda x: x.lab_no, self.related_instances(Sample)))
        sv_df = variant_df[variant_df.Sample.isin(lab_nos)]
        df_rows = tqdm(list(sv_df.iterrows()), leave=False)
        for index, row in df_rows:
            db_build = self.related_instance(
                GenomeBuild,
                filters={'name': row.build}
            )
            variant_f = {
                "chrom": row.CHROM,
                "pos": row.POS,
                "ref": row.REF,
                "alt": row.ALT,
                "genome_build_id": db_build.id
            }
            vcf_f = {"path": row.VCF}
            db_variant = self.related_instance(Variant, filters=variant_f)
            db_vcf = self.related_instance(VCF, filters=vcf_f)

            variant_report = {
                "variant": db_variant,
                "vcf": db_vcf,
                "qual": None if pd.isnull(row.QUAL) else row.QUAL,
                "filter_pass": None,
                "depth": row.DEPTH
            }
            variant_reports.append(variant_report)
        df_rows.close()
        return variant_reports

    def get_variant_report_info(self, filters=False) -> List[Dict[str, Any]]:
        variant_report_values = []
        variant_manager = self.run.multiple_run_adder.variant_manager
        variant_df = variant_manager.variant_df.drop_duplicates(
            subset=["Sample", "CHROM", "POS", "REF", "ALT", "build"]
        )
        lab_nos = list(map(lambda x: x.lab_no, self.related_instances(Sample)))
        sv_df = variant_df[variant_df.Sample.isin(lab_nos)]
        df_rows = tqdm(list(sv_df.iterrows()), leave=False)
        for index, row in df_rows:
            db_build = self.related_instance(
                GenomeBuild,
                filters={'name': row.build}
            )
            variant_f = {
                "chrom": row.CHROM,
                "pos": row.POS,
                "ref": row.REF,
                "alt": row.ALT,
                "genome_build_id": db_build.id
            }
            vcf_f = {"path": row.VCF}
            db_variant = self.related_instance(Variant, filters=variant_f)
            db_vcf = self.related_instance(VCF, filters=vcf_f)
            vr_f = {'variant_id': db_variant.id, 'vcf_id': db_vcf.id}
            db_variant_report = self.related_instance(
                VariantReport,
                filters=vr_f
            )

            if filters:
                keys = variant_manager.filter_keys
            else:
                keys = variant_manager.info_keys
            for key in keys:
                # don't bother adding passes or null values to db
                if filters and row[key] == False: continue
                if not filters and str(row[key]) == 'nan': continue

                variant_report_value = {
                    'variant_report': db_variant_report,
                    'tag': key.split('|')[1],
                    'description': key.split('|')[-1],
                    'value': row[key]
                }
                variant_report_values.append(variant_report_value)

        df_rows.close()
        return variant_report_values

    def get_variant_report_filter(self) -> List[Dict[str, Any]]:
        return self.get_variant_report_info(filters=True)

    def get_exon_report(self, exon=True) -> List[Dict[str, Any]]:
        reports = []

        db_excel_reports = self.related_instances(ExcelReport)
        # loop through excel reports and initialise as df
        for db_excel_report in tqdm(db_excel_reports, leave=False):
            wb = load_workbook(
                filename=db_excel_report.path,
                data_only=True,
                read_only=True
            )
            sheet = wb['Coverage-exon'] if exon else wb['Coverage-gene']
            report_df = pd.DataFrame(sheet.values)
            # set header as first row
            report_df.columns = report_df.iloc[0]
            report_df = report_df[1:]

            # get the custom threshold values in this excelreport
            thresholds = tuple(
                map(
                    # eg. 10x 20x 100x -> [10, 20, 100]
                    lambda x: int(x.strip('x')),
                    report_df.filter(regex='^\d+x$').columns
                )
            )
            for index, row in report_df.iterrows():
                # fetch the counts and pcts for this entry
                threshold_counts = tuple(
                    map(
                        lambda threshold: row[f'{threshold}x'],
                        thresholds
                    )
                )
                threshold_pcts = tuple(
                    map(
                        lambda threshold: row[f'pct>{threshold}x'],
                        thresholds
                    )
                )
                report = {
                    'excel_report': db_excel_report,
                    'cov_min': row['Min'],
                    'cov_max': row['Max'],
                    'cov_mean': row['Mean'],
                    'cov_region': row['region'],
                    'cov_thresholds': thresholds,
                    'cov_count_at_threshold': threshold_counts,
                    'cov_pct_above_threshold': threshold_pcts
                }
                if exon:
                    refseq_id = '_'.join(row['Transcript'].split('_')[:2])
                    tx_f = {'refseq_id': refseq_id}
                    db_tx = self.related_instance(Transcript, filters=tx_f)
                    exon_f = {'transcript_id': db_tx.id, 'number': row['Exon']}
                    exon_f['number'] = str(exon_f['number'])
                    db_exon = self.related_instance(Exon, filters=exon_f)
                    report['exon'] = db_exon
                    report['tag'] = '_'.join(row['Transcript'].split('_')[2:])
                elif row['Gene']:
                    refseq_id = '_'.join(row['Transcript'].split('_')[:2])
                    tx_f = {'refseq_id': refseq_id}
                    db_tx = self.related_instance(Transcript, filters=tx_f)
                    gene_f = {'hgnc_name': row['Gene']}
                    db_gene = self.related_instance(Gene, filters=gene_f)
                    report['gene'] = db_gene
                    report['transcript'] = db_tx
                    report['tag'] = '_'.join(row['Transcript'].split('_')[2:])
                else:
                    continue
                reports.append(report)
        return reports

    def get_gene_report(self) -> List[Dict[str, Any]]:
        return self.get_exon_report(exon=False)