# Generated by Django 3.1.6 on 2021-05-11 16:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('db', '0013_pipelinesection_section'),
    ]

    operations = [
        migrations.AddField(
            model_name='section',
            name='slug',
            field=models.SlugField(null=True, unique=True),
        ),
    ]
