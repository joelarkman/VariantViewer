# Generated by Django 3.1.6 on 2021-04-28 09:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_auto_20210427_1253'),
    ]

    operations = [
        migrations.AddField(
            model_name='userfilter',
            name='selected',
            field=models.BooleanField(default=False),
        ),
    ]
