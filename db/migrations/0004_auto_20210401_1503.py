# Generated by Django 3.1.6 on 2021-04-01 15:03

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('db', '0003_auto_20210326_0941'),
    ]

    operations = [
        migrations.AddField(
            model_name='samplesheet',
            name='latest_run',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='latest', to='db.run'),
        ),
        migrations.AlterField(
            model_name='run',
            name='samplesheet',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='runs', to='db.samplesheet'),
        ),
    ]
