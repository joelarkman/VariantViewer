# Generated by Django 3.1.6 on 2021-05-21 19:33

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('db', '0016_merge_20210513_1155'),
        ('web', '0011_auto_20210519_1003'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='comment',
            options={'ordering': ['classification']},
        ),
        migrations.AlterModelOptions(
            name='document',
            options={'ordering': ['-date_created']},
        ),
        migrations.AlterUniqueTogether(
            name='document',
            unique_together={('sample_transcript_variant', 'document')},
        ),
    ]
