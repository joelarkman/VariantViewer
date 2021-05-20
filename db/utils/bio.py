import csv
import re
import tempfile
from typing import List

import pandas as pd
import vcf as py_vcf


class VariantManager:
    """Collects information about all variants in a MRA operation into a csv.

    Allows storing  of information eg. sample, coordinates, of a variant whilst
    the initial model is saved to then come back and save/relate this info at a
    later time.

    the csv CANNOT BE LOADED in one, use pd.read_csv(use_cols=[]) arg to reduce
    memory footprint
    """
    def __init__(self):
        self.re_ln = re.compile('(D\d{2})-(\d{5})')

        self.started_write = False
        self.record_csv = tempfile.NamedTemporaryFile(delete=False)
        self.record_csv.close()
        print(self.record_csv.name)

    def update_records(self, vcf_filename):
        reader = py_vcf.Reader(filename=vcf_filename, encoding='utf-8')
        if not self.started_write:
            keys = reader.infos['CSQ'].desc.split('Format: ')[-1].split('|')
            headers = ["Sample", "CHROM", "POS", "REF", "ALT"] + keys
            with open(self.record_csv.name, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(headers)
            self.started_write = True
        vcf_values = []
        for record in reader:
            sample = '.'.join(self.re_ln.search(record.samples[0].sample).groups())
            chrom = record.CHROM
            pos = record.POS
            ref = record.REF
            alt = record.ALT
            variant_info = [sample, chrom, pos, ref, alt]
            values = [csq.split('|') for csq in record.INFO['CSQ']]
            vcf_values.extend(variant_info + values)
            del record
        with open(self.record_csv.name, 'a', newline='') as f:
            writer = csv.writer(f)
            for value in vcf_values:
                writer.writerow(value)
        # noinspection PyProtectedMember
        reader._reader.close()
