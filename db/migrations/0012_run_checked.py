# Generated by Django 3.1.6 on 2021-05-11 13:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('db', '0011_auto_20210507_0933'),
    ]

    operations = [
        migrations.AddField(
            model_name='run',
            name='checked',
            field=models.BooleanField(default=False),
        ),
    ]
