# Generated by Django 3.1.6 on 2021-03-25 13:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('db', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='run',
            name='qc_status',
            field=models.IntegerField(choices=[(0, 'Pending'), (1, 'Pass'), (2, 'Fail')], default=0),
        ),
    ]
