# Generated by Django 3.1.6 on 2021-09-14 13:58

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('db', '0035_auto_20210913_1100'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='genecoveragethreshold',
            unique_together=None,
        ),
        migrations.RemoveField(
            model_name='genecoveragethreshold',
            name='gene_report',
        ),
        migrations.AddField(
            model_name='exonreport',
            name='cov_count_at_threshold',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.IntegerField(), default=None, size=None),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='exonreport',
            name='cov_pct_above_threshold',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.IntegerField(), default=None, size=None),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='exonreport',
            name='cov_thresholds',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.IntegerField(), default=None, size=None),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='genereport',
            name='cov_count_at_threshold',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.IntegerField(), default=None, size=None),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='genereport',
            name='cov_pct_above_threshold',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.IntegerField(), default=None, size=None),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='genereport',
            name='cov_thresholds',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.IntegerField(), default=None, size=None),
            preserve_default=False,
        ),
        migrations.DeleteModel(
            name='ExonCoverageThreshold',
        ),
        migrations.DeleteModel(
            name='GeneCoverageThreshold',
        ),
    ]
