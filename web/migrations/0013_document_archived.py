# Generated by Django 3.1.6 on 2021-05-25 13:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('web', '0012_auto_20210521_1933'),
    ]

    operations = [
        migrations.AddField(
            model_name='document',
            name='archived',
            field=models.BooleanField(default=False),
        ),
    ]