# Generated by Django 3.1.4 on 2021-05-07 09:33

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('db', '0010_auto_20210427_1253'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sample',
            name='patient',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='samples', to='db.patient'),
        ),
    ]
