# Generated by Django 3.1.6 on 2021-06-25 11:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('db', '0029_auto_20210624_1510'),
    ]

    operations = [
        migrations.AddField(
            model_name='exonreport',
            name='tag',
            field=models.CharField(default=None, max_length=255),
            preserve_default=False,
        ),
    ]
