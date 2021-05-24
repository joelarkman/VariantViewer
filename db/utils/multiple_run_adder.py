from typing import List

import pandas as pd

from VariantViewer.utils.notebook import is_notebook

if is_notebook():
    from tqdm.notebook import tqdm
else:
    from tqdm import tqdm

from db.models import *
from db.utils.bio import VariantManager
from db.utils.run_attribute_manager import RunAttributeManager
from db.utils.run_builder import RunBuilder
from db.utils.run_model import RunModel


class MultipleRunAdder:
    """
    Manager class for overseeing the addition of multiple pipeline runs.

    Takes list of files denoted the commandline usage for a run in the
    output directory and fetches relevant info for addition to tables. This is
    done in bulk by creating sets of complete data for each table in sequence
    according to an update order based on db dependencies.

    TODO:
        - allow for binning
        - skip already present files
        - postprocess function: add pipeline version update checks
        - postprocess function: create symlinks
        - make into an atomic transaction
    """

    def __init__(self, commandline_usage_list):
        self.commandline_usage_list = commandline_usage_list
        self.df = pd.DataFrame()
        self.variant_manager = VariantManager()
        self.lookup_index = {}
        self.runs = []

    def update_database(self):
        self.runs = [
            # create a RunBuilder for each detected run
            RunBuilder(commandline_usage_file, self)
            for commandline_usage_file
            in self.commandline_usage_list
        ]

        # make a dataframe of the base run data
        columns = [
            'pipeline', 'pipeline_version', 'worksheet', 'interop_dir',
            'fastq_dir', 'output_dir', 'completed_at', 'samplesheet'
        ]
        data = []
        for run in self.runs:
            data.append([
                run.pipeline,
                run.version,
                run.worksheet,
                run.interop_dir,
                run.fastq_dir,
                run.output_dir,
                run.completed_at,
                run.samplesheet,
            ])
        self.df = pd.DataFrame(columns=columns, data=data)

        # begin the process of bulk adding info to the database
        self.add_runs(self.runs)

    def add_runs(self, runs):
        """The bulk update process.

        Loops through each model type, then for each case invokes an attribute
        manager to fetch the corresponding data for that case. Once there is a
        set of data for that model for each case in the process, it will commit
        to the DB and then move on to the next model type.

        Two things to note: (1) the update must happen in a particular order due
        to relational dependencies in the database (ie. can't create a Sample if
        there is no SampleSheet for it to be created on). and (2) there will be
        some models in which there are MANY INSTANCES to be created, rather than
        just 1 per case.
        """
        to_update = tqdm(self.update_order(), desc="Updating...", leave=False)
        for update_t in to_update:
            # create a bulk set of all data for each model type in sequence
            model_type, many = update_t
            managed = model_type in self.managed_fields
            model_list: List[RunModel] = []

            # noinspection PyProtectedMember
            to_update.set_description(f"Parsing {model_type._meta.model_name}")
            # ensure run order is consistent
            runs = tuple(runs)
            tqdm_runs = tqdm(runs, desc=f"Run...", leave=False)

            for run in tqdm_runs:
                tqdm_runs.set_description(f"{run.full_name}")
                # fetch the data from this run for this particular model type
                model_objects = model_type.objects.all()
                # create attribute managers corresponding to the current model
                attribute_manager = RunAttributeManager(
                    run=run,
                    model_type=model_type,
                    instances=model_objects,
                    many=many
                )
                run.attribute_managers[model_type] = attribute_manager
                if many:
                    model_list.extend(attribute_manager.run_model.run_models)
                else:
                    model_list.append(attribute_manager.run_model)

                # only run managed fields (eg. VariantManager-managed) once
                if managed:
                    break
            runs.close()

            if managed:
                # ensure all runs have access to the same managed run attributes
                for run in runs[1:]:
                    managed_attr_mgr = runs[0].attribute_managers[model_type]
                    run.attribute_managers[model_type] = managed_attr_mgr

            # do the creation then refresh the attribute managers
            self.bulk_create_new(model_type, model_list)
            for model in model_list:
                model.check_found_in_db()
        to_update.close()

    @staticmethod
    def bulk_create_new(model_type, model_list: list) -> None:
        """Create then commit a unique set of attrs for a list of new instances

        Args:
            model_type: the database model type being updated
            model_list: the list of instances which are involved in the update
        """
        attr_list = [model.attrs for model in model_list if not model.entry]

        # remove dup, eg. same variant across cases, by setting tuples of values
        attr_list = [
            dict(attr_t) for attr_t
            in set([
                tuple(attr_d.items())
                for attr_d in attr_list
            ])
        ]

        to_create = [model_type(**attrs) for attrs in attr_list]
        model_type.objects.bulk_create(to_create)

    @staticmethod
    def update_order():
        """create a tuple of tuples to inform the order of updating

        each sub-tuple is:
        [0] a key to access an attribute manager for a case
        [1] whether that corresponding model has many instances per run
        """
        return (
            (Pipeline, False),
            (PipelineVersion, False),
            (Samplesheet, False),
            (Run, False),
            # patient info
            # (Patient, True),
            (Sample, True),
            (SamplesheetSample, True),
            (BAM, True),
            (SampleBAM, True),
            (VCF, True),
            (SampleVCF, True),
            (ExcelReport, True),
            # gene info
            (Gene, True),
            (Transcript, True),
            (Exon, True),
            # variant info
            (Variant, True),
            (SampleVariant, True),
            (TranscriptVariant, True),
            (SampleTranscriptVariant, True),
            # coordinate info
            (GenomeBuild, True),
            (GenomicCoordinate, True),
            (VariantCoordinate, True),
            (Sequence, True),
            (ExonSequence, True),
            # vcf info
            (VariantReport, True),
            (VariantReportInfo, True),
            (VariantReportFilter, True),
            # coverage info
            (CoverageInfo, True),
            (ExonReport, True),
            (GeneReport, True),
        )

    @property
    def managed_fields(self):
        return (
            Gene,
            Exon,
            Transcript,
            Variant
        )
