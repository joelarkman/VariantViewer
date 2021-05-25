import csv
import re
import tempfile

import pandas as pd
import vcf as py_vcf


class VariantManager:
    """Collects information about all variants in a MRA operation into a csv.

    Allows storing  of information eg. sample, coordinates, of a variant whilst
    the initial model is saved to then come back and save/relate this info at a
    later time.

    Also stores when genes, transcripts, and exons have been accessed from the
    csv as these don't need to be accessed for every single run; the data is the
    same.

    the csv CANNOT BE LOADED in one, use pd.read_csv(use_cols=[]) arg to reduce
    memory footprint
    """

    def __init__(self):
        self.re_ln = re.compile('(D\d{2})-(\d{5})')

        self.started_write = False
        self.record_csv = tempfile.NamedTemporaryFile(delete=False)
        self.record_csv.close()

        # various dataframes for accessing data without bloating memory
        self._gene_df = pd.DataFrame()
        self._transcript_df = pd.DataFrame()
        self._variant_df = pd.DataFrame()
        self._transcript_variant_df = pd.DataFrame()

    def update_records(self, vcf_filename):
        """Add the records from a given VCF to the managed CSV of variant info.
        """
        reader = py_vcf.Reader(filename=vcf_filename, encoding='utf-8')
        if not self.started_write:
            # set the headers of the csv file if haven't done so already
            keys = reader.infos['CSQ'].desc.split('Format: ')[-1].split('|')
            headers = ["Sample", "CHROM", "POS", "REF", "ALT"] + keys
            with open(self.record_csv.name, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(headers)
            self.started_write = True

        vcf_values_list = []
        for record in reader:
            # loop through the VCF records using the PyVCF module
            record_sample = record.samples[0].sample
            # set the sample + variant info
            sample = '.'.join(self.re_ln.search(record_sample).groups())
            chrom = record.CHROM
            pos = record.POS
            ref = record.REF
            alt = record.ALT
            # list of lists: each sublist is a list of consequences for the var
            values = [csq.split('|') for csq in record.INFO['CSQ']]
            for csq in values:
                variant_info = [sample, chrom, pos, ref, alt]
                variant_info.extend(csq)
                # add a potential consequence for a variant to the main list
                vcf_values_list.append(variant_info)
            # manage memory
            del record

        with open(self.record_csv.name, 'a+', newline='') as f:
            # with a list of all consequences for all variants, write to csv
            writer = csv.writer(f)
            writer.writerows(vcf_values_list)

        # noinspection PyProtectedMember
        reader._reader.close()

    def get_df_info(self, cols, dtypes=None, converters=None):
        return pd.read_csv(
            self.record_csv.name,
            usecols=cols,
            dtype=dtypes,
            converters=converters
        )

    @property
    def gene_df(self):
        if self._gene_df.empty:
            # read only HGNC_ID and Gene Symbol values from csv
            cols = {"SYMBOL": "category", "Gene": pd.UInt32Dtype()}
            # exclude those without hgnc ID values
            df = self.get_df_info(cols=cols.keys(), dtypes=cols)
            self._gene_df = df[df.Gene.notna()].drop_duplicates()
        return self._gene_df

    @property
    def transcript_df(self):
        if self._transcript_df.empty:
            df = self.get_df_info(
                # read the hgnc_id, feature type, refseq ID, and canon status
                cols=["Gene", "Feature_type", "Feature", "CANONICAL", "EXON"],
                dtypes={
                    "Gene": pd.UInt32Dtype(),
                    "Feature_type": "category",
                    "Feature": "category"
                },
                converters={
                    "CANONICAL": lambda x: True if x == "YES" else False,
                    # also display exon count for transcripts if present
                    "EXON": lambda x: 0 if not x else int(x.split('/')[-1])
                }
            )
            self._transcript_df = df[
                # only include those with hgnc id
                (df.Gene.notna())
                # only include those which are transcripts (ie not regulatory)
                & (df.Feature_type == "Transcript")
                ].sort_values(
                # sort on exon count, to ensure duplicates with count are kept
                "EXON",
                ascending=False
            ).drop_duplicates(
                subset=["Gene", "Feature"]
            )
        return self._transcript_df

    @property
    def variant_df(self):
        if self._variant_df.empty:
            df = self.get_df_info(
                cols=[
                    "REF",
                    "ALT",
                    "Sample",
                    "Feature_type",
                    "Feature",
                    "HGVSc",
                    "HGVSp",
                    "Consequence",
                    "CANONICAL",
                ],
                dtypes={
                    "REF": "category",
                    "Feature_type": "category",
                    "Feature": "category",
                    "Sample": "category",
                    "HGVSc": "category",
                    "HGVSp": "category",
                    "Consequence": "category",
                    "IMPACT": "category",
                },
                converters={
                    "ALT": lambda x: x.strip('[]'),
                    "CANONICAL": lambda x: True if x == "YES" else False,
                }
            )
            self._variant_df = df
        return self._variant_df

    @property
    def transcript_variant_df(self):
        if self._transcript_variant_df.empty:
            df = self.variant_df
            self._transcript_variant_df = df[
                (df.Gene.notna())
                & (df.Feature_type == "Transcript")
            ].drop_duplicates(
                subset=["Feature", "REF", "ALT"]
            )
        return self._transcript_variant_df