# Generated by Django 3.1.6 on 2021-04-22 12:43

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('db', '0007_sample_patient'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bam',
            name='run',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='db.run'),
        ),
    ]
