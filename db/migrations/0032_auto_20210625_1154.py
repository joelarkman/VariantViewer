# Generated by Django 3.1.6 on 2021-06-25 11:54

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('db', '0031_auto_20210625_1154'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='exonreport',
            unique_together={('excel_report', 'exon', 'tag')},
        ),
    ]