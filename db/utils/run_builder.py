from __future__ import annotations
from pathlib import Path
from typing import Type
from typing import TypedDict

from django.db import models


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from db.utils.multiple_run_adder import MultipleRunAdder
    from db.utils.run_attribute_manager import RunAttributeManager


class RunBuilder:
    """ Class to  build run data (RAM) for db addition (MRA)
    
    This module contains the information pertinent to a single run. It also
    HAS-A dictionary of RunAttributeManager classes which are managed by the
    MultipleRunAdder manager class, which contain information pertinent to db
    models which are related to the run.
    
    Attributes:
    """
    def __init__(self, commandline_usage_file, mra: MultipleRunAdder):
        self.commandline_usage_file = commandline_usage_file
        self.multiple_run_adder = mra
        self.commandline_usage = self.parse_commandline_usage()
        self.pipeline, self.worksheet, self.version = self.get_run_info()
        self.interop_dir, self.fastq_dir = self.get_input_dirs()
        self.output_dir = self.get_output_dir()
        self.completed_at = self.get_completed_at()
        self.samplesheet = self.get_samplesheet()
        self.attribute_managers = AttributesManagersDict()

    def parse_commandline_usage(self):
        """Take a commandline usage file and parse arguments as a list."""
        with open(self.commandline_usage_file, 'r') as f:
            commandline_usage = list(
                filter(
                    # filter out blanklines
                    None,
                    # strip newlines
                    map(lambda x: x.strip(), f.readlines())
                )
            )
        if (len(commandline_usage) - 1) % 16 == 0:
            # should be 16 args for UMP, else take header + last 16
            commandline_usage = [commandline_usage[0]] + commandline_usage[-16:]

        return commandline_usage

    def get_run_info(self):
        """Extract information about the run from its commandline usage args"""
        try:
            run_info_tup = self.commandline_usage_file.parent.name.split('_')
            pipeline, worksheet, version = run_info_tup[0:3]

        except ValueError as e:
            # improper folder structure
            if "not enough values to unpack" not in str(e):
                raise e
            # extract info from the commandline usage
            # and which config file was used
            worksheet = self.commandline_usage_file.parts[-2]
            config_file = self.commandline_usage[-11].split('/')
            pipeline = config_file[-1].split('-')[0]
            version = config_file[3].split('-')[-1]
        return pipeline, worksheet, version

    def get_input_dirs(self):
        """Extract the FASTQ and InterOp directories for the run from CL args"""
        fastq_index = -7
        interop_index = -5
        return self.commandline_usage[interop_index], \
               self.commandline_usage[fastq_index]

    def get_output_dir(self):
        """Extract the output directory based on the location of the CL file"""
        output_dir = Path(self.commandline_usage_file).parent
        return output_dir

    def get_completed_at(self):
        """Leverage PathLib to determine the pipeline complete time"""
        complete_file = self.output_dir / 'pipeline-complete.txt'
        assert complete_file.exists(), f"No such file: {complete_file}"
        return complete_file.stat().st_mtime

    def get_samplesheet(self):
        """Get the filepath to the samplesheet used for this run."""
        samplesheet_index = -9
        return self.commandline_usage[samplesheet_index]

    @property
    def full_name(self):
        return f"{self.pipeline}_{self.version}_{self.worksheet}"

    @property
    def bam_dir(self):
        # noinspection SpellCheckingInspection
        bam_dirs = list(self.output_dir.glob('*[Aa]lignment*'))
        assert len(list(bam_dirs)) < 2, f"Multiple BAM dirs for {self.full_name}"
        assert len(list(bam_dirs)) != 0, f"No BAM dir for {self.full_name}"
        return bam_dirs[0]

    @property
    def vcf_dir(self):
        vcf_dirs = list(self.output_dir.glob('*[Vv][Cc][Ff]*'))
        assert len(list(vcf_dirs)) < 2, f"Multiple VCF dir for {self.full_name}"
        assert len(list(vcf_dirs)) != 0, f"No VCF dir for {self.full_name}"
        return vcf_dirs[0]

    @property
    def excel_dir(self):
        # noinspection SpellCheckingInspection
        excel_dirs = list(self.output_dir.glob('*[Ee]xcel*'))
        assert len(list(excel_dirs)) < 2, f"Multiple XL dir: {self.full_name}"
        assert len(list(excel_dirs)) != 0, f"No XL dir for {self.full_name}"
        return excel_dirs[0]


class AttributesManagersDict(TypedDict):
    Type[models.Model]: RunAttributeManager