# Generated by Django 3.1.6 on 2021-07-28 14:52

import accounts.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0005_user_default_section'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='validate_hash',
            field=models.CharField(default=accounts.models.get_validate_hash, max_length=255),
        ),
    ]