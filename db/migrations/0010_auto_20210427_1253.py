# Generated by Django 3.1.6 on 2021-04-27 12:53

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('web', '0007_auto_20210427_1240'),
        ('db', '0009_auto_20210427_1240'),
    ]

    operations = [
        migrations.CreateModel(
            name='VCFFilter',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('date_modified', models.DateTimeField(auto_now=True)),
                ('filter', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='web.filter')),
                ('vcf', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='db.vcf')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='vcf',
            name='filters',
            field=models.ManyToManyField(through='db.VCFFilter', to='web.Filter'),
        ),
    ]
