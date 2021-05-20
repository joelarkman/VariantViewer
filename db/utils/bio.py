import re
from typing import List

import pandas as pd
import vcf as py_vcf


class VariantManager:
    """Holds collected information about all variants in a MRA operation.

    Allows caching of information eg. sample, coordinates, of a variant whilst
    the initial model is saved to then come back and save/relate this info at a
    later time.
    """
    def __init__(self, *args, **kwargs):
        # noinspection PyProtectedMember,PyUnresolvedReferences
        self.records: List[py_vcf.model._Record] = []
        self.csq_keys: list = []
        self._df: pd.DataFrame = pd.DataFrame()

    def create_df(self):
        self.csq_keys = ["Sample", "CHROM", "POS", "REF", "ALT"] + self.csq_keys
        csq_values = []
        for record in self.records:
            pattern = re.compile(r'(D\d{2})-(\d{5})')
            sample = '.'.join(pattern.search(record.samples[0].sample).groups())
            chrom = record.CHROM
            pos = record.POS
            ref = record.REF
            alt = record.ALT

            value_lists = [csq.split('|') for csq in record.INFO['CSQ']]
            for value_list in value_lists:
                csq_values.append([sample, chrom, pos, ref, alt] + value_list)
        return pd.DataFrame(data=self.csq_keys, columns=csq_values)

    @property
    def df(self):
        if self._df.empty:
            self._df = self.create_df()
        return self._df