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
        # TODO: unleash the kraken
        # self.add_runs(runs)

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

        for model_type, many in self.update_order():
            # create a bulk set of all data for each model type in sequence
            for run in tqdm(runs, desc=f"parsing {model_type.__name__} to db"):
                tqdm.set_description(run.full_name)

                # fetch the data from this run for this particular model type
                model_objects = model_type.objects.all()

                # create attribute managers corresponding to the current model
                run.attribute_managers[model_type] = RunAttributeManager(
                    run=run,
                    model_type=model_type,
                    instances=model_objects
                )

            # create a list of models to be created
            if not many:
                model_list = [
                    run.attribute_managers[model_type].run_model
                    for run in runs
                ]
            else:
                model_lists = [
                    run.attribute_managers[model_type].run_model.run_models
                    for run in runs
                ]
                # flatten list of lists
                model_list = [
                    model for model_list in model_lists for model in model_list
                ]

            # do the creation then refresh the attribute managers
            self.bulk_create_new(model_type, model_list)
            for model in model_list:
                model.check_found_in_db()

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
            (Patient, True),
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
