# Generated by Django 3.1.6 on 2021-05-21 13:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('db', '0017_merge_20210521_1210'),
    ]

    operations = [
        migrations.AlterField(
            model_name='run',
            name='command_line_usage',
            field=models.TextField(),
        ),
    ]
