import csv
import os
import re
import tempfile

import pandas as pd
import vcf as py_vcf


CHROM_PATTERN = re.compile(r'chr(..?)')


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
        self.keys = []
        self.record_csv = tempfile.NamedTemporaryFile(delete=False)
        self.record_csv.close()

        # various dataframes for accessing data without bloating memory
        self._gene_df = pd.DataFrame()
        self._transcript_df = pd.DataFrame()
        self._variant_df = pd.DataFrame()
        self._transcript_variant_df = pd.DataFrame()

    def delete_csv(self):
        os.remove(self.record_csv.name)

    def update_records(self, vcf_filename):
        """Add the records from a given VCF to the managed CSV of variant info.
        """
        reader = py_vcf.Reader(filename=vcf_filename, encoding='utf-8')
        info = reader.infos
        skip = ['CSQ',]
        filters = reader.filters
        info_keys = [
            header for header
            in map(
                # get all headers except CSQ, which is handled separately
                lambda x: None if x.id in skip else f"INFO|{x.id}|{x.desc}",
                info.values()
            )
            if header is not None
        ]
        filter_keys = [
            header for header in map(
                lambda x: f"FILTER|{x.id}|{x.desc}",
                filters.values()
            )
        ]
        vep_meta = reader.metadata.get('VEP')[0]
        build_re = re.compile(r'assembly="?([^"]+)"?')
        build = build_re.search(vep_meta).groups()[0]
        vep = vep_meta.split(' ')[0].strip('"')
        file_format = list(reader.metadata.values())[0]

        if not self.started_write:
            # set the headers of the csv file if haven't done so already
            csq_keys = info['CSQ'].desc.split('Format: ')[-1].split('|')
            var_keys = ["CHROM", "POS", "REF", "ALT", "QUAL", "DEPTH", "PF"]
            meta_keys = ["Sample", "VCF", "format", "VEP", "build"]

            headers = meta_keys + var_keys + csq_keys + info_keys + filter_keys
            with open(self.record_csv.name, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(headers)
            self.started_write = True
            self.keys = headers

        vcf_values_list = []
        for record in reader:
            # loop through the VCF records using the PyVCF module
            record_sample = record.samples[0].sample
            # set the sample + variant info
            sample = '.'.join(self.re_ln.search(record_sample).groups())
            meta = [sample, vcf_filename, file_format, vep, build]

            chrom = record.CHROM
            pos = record.POS
            ref = record.REF
            alt = record.ALT
            qual = record.QUAL
            # add depth and pf here since we use it in the VariantReport model
            depth = record.INFO.get('DP')
            pf = True if record.FILTER in ['.', 'PASS'] else False
            var = [chrom, pos, ref, alt, qual, depth, pf]

            # fetch the INFO information for the variant, match to INFO headers
            var_info = [
                record.INFO.get(key.split('|')[1])
                for key in info_keys
            ]

            # create a of True/False for whether a filter from header applies
            filters = record.FILTER
            f = lambda x: False if not filters else x.split('|')[1] in filters
            var_filters = list(map(f, filter_keys))

            # deal with the consequence INFO field from VEP
            consequences = [csq.split('|') for csq in record.INFO['CSQ']]
            for csq in consequences:
                # add a potential consequence for a variant to the main list
                variant_info = meta + var + csq + var_info + var_filters
                vcf_values_list.append(variant_info)

            # manage memory
            del record

        # open the file in a+ so as to seek to end, do not load file in RAM
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
                cols=[
                    "build",
                    "Gene",
                    "Feature_type",
                    "Feature",
                    "CANONICAL",
                    "EXON"
                ],
                dtypes={
                    "build": "category",
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
                    "build",
                    "CHROM",
                    "POS",
                    "REF",
                    "ALT",
                    "QUAL",
                    "DEPTH",
                    "PF",
                    "Sample",
                    "Gene",
                    "SYMBOL",
                    "Feature_type",
                    "Feature",
                    "HGVSc",
                    "HGVSp",
                    "Consequence",
                    "IMPACT",
                    "CANONICAL",
                ],
                dtypes={
                    "build": "category",
                    "POS": pd.UInt32Dtype(),
                    "REF": "category",
                    "QUAL": pd.UInt32Dtype(),
                    "DEPTH": pd.UInt16Dtype(),
                    "PF": "boolean",
                    "Feature_type": "category",
                    "Feature": "category",
                    "Sample": "category",
                    "Gene": pd.UInt32Dtype(),
                    "SYMBOL": "category",
                    "HGVSc": "category",
                    "HGVSp": "category",
                    "Consequence": "category",
                    "IMPACT": "category",
                },
                converters={
                    "CHROM": lambda x: CHROM_PATTERN.match(x).groups()[0],
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