# Generated by Django 3.1.6 on 2021-05-21 11:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('db', '0014_remove_transcript_sequence'),
    ]

    operations = [
        migrations.AlterField(
            model_name='gene',
            name='hgnc_id',
            field=models.CharField(max_length=255, unique=True),
        ),
        migrations.AlterField(
            model_name='genomebuild',
            name='path',
            field=models.TextField(unique=True),
        ),
        migrations.AlterField(
            model_name='pipeline',
            name='name',
            field=models.CharField(max_length=255, unique=True),
        ),
        migrations.AlterField(
            model_name='sample',
            name='lab_no',
            field=models.CharField(max_length=50, unique=True),
        ),
        migrations.AlterField(
            model_name='samplesheet',
            name='path',
            field=models.CharField(max_length=255, unique=True),
        ),
        migrations.AlterField(
            model_name='transcript',
            name='refseq_id',
            field=models.CharField(max_length=255, unique=True),
        ),
        migrations.AlterUniqueTogether(
            name='exon',
            unique_together={('transcript', 'number')},
        ),
        migrations.AlterUniqueTogether(
            name='exonreport',
            unique_together={('excel_report', 'exon')},
        ),
        migrations.AlterUniqueTogether(
            name='exonsequence',
            unique_together={('exon', 'sequence')},
        ),
        migrations.AlterUniqueTogether(
            name='genereport',
            unique_together={('excel_report', 'gene')},
        ),
        migrations.AlterUniqueTogether(
            name='genomiccoordinate',
            unique_together={('chrom', 'pos')},
        ),
        migrations.AlterUniqueTogether(
            name='pipelineversion',
            unique_together={('version', 'pipeline')},
        ),
        migrations.AlterUniqueTogether(
            name='sampletranscriptvariant',
            unique_together={('transcript', 'sample_variant')},
        ),
        migrations.AlterUniqueTogether(
            name='samplevariant',
            unique_together={('sample', 'variant')},
        ),
        migrations.AlterUniqueTogether(
            name='sequence',
            unique_together={('strand', 'start_coord', 'end_coord')},
        ),
        migrations.AlterUniqueTogether(
            name='transcriptvariant',
            unique_together={('transcript', 'variant')},
        ),
        migrations.AlterUniqueTogether(
            name='variantcoordinate',
            unique_together={('variant', 'coordinate')},
        ),
        migrations.AlterUniqueTogether(
            name='variantreport',
            unique_together={('variant', 'vcf')},
        ),
        migrations.AddIndex(
            model_name='bam',
            index=models.Index(fields=['path'], name='db_bam_path_ca8d57_idx'),
        ),
        migrations.AddIndex(
            model_name='excelreport',
            index=models.Index(fields=['path'], name='db_excelrep_path_65ed49_idx'),
        ),
        migrations.AddIndex(
            model_name='genomiccoordinate',
            index=models.Index(fields=['chrom', 'pos'], name='db_genomicc_chrom_c51274_idx'),
        ),
        migrations.AddIndex(
            model_name='sample',
            index=models.Index(fields=['lab_no'], name='db_sample_lab_no_13fdaa_idx'),
        ),
        migrations.AddIndex(
            model_name='sampletranscriptvariant',
            index=models.Index(fields=['transcript', 'sample_variant'], name='db_sampletr_transcr_f6d75a_idx'),
        ),
        migrations.AddIndex(
            model_name='sequence',
            index=models.Index(fields=['start_coord'], name='db_sequence_start_c_b46bc9_idx'),
        ),
        migrations.AddIndex(
            model_name='sequence',
            index=models.Index(fields=['end_coord'], name='db_sequence_end_coo_822d0a_idx'),
        ),
        migrations.AddIndex(
            model_name='transcriptvariant',
            index=models.Index(fields=['transcript', 'variant'], name='db_transcri_transcr_c271a8_idx'),
        ),
        migrations.AddIndex(
            model_name='variantcoordinate',
            index=models.Index(fields=['variant', 'coordinate'], name='db_variantc_variant_e78774_idx'),
        ),
        migrations.AddIndex(
            model_name='vcf',
            index=models.Index(fields=['path'], name='db_vcf_path_4f84e7_idx'),
        ),
    ]
