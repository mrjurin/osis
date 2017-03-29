# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2017-03-16 12:32
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion

from internship.models.cohort import Cohort
from internship.models.period import Period

def create_the_first_cohort(apps, schema_editor):
    Cohort.objects.create(name='Cohort 1')


def assign_first_cohort_to_periods(apps, schema_editor):
    cohort = Cohort.objects.first()
    for period in Period.objects.all():
        period.cohort = cohort
        period.save()

class Migration(migrations.Migration):

    dependencies = [
        ('base', '0098_auto_20170306_0953'),
        ('internship', '0034_internshipenrollment_internship_choice'),
    ]

    operations = [
        migrations.CreateModel(
            name='Cohort',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=64)),
                ('description', models.TextField()),
                ('students', models.ManyToManyField(to='base.Student')),
            ],
        ),
        migrations.RunPython(create_the_first_cohort),
        migrations.AddField(
            model_name='period',
            name='cohort',
            field=models.ForeignKey(null=True, default=None, on_delete=django.db.models.deletion.CASCADE, to='internship.Cohort'),
            preserve_default=False,
        ),
        migrations.RunPython(assign_first_cohort_to_periods),
        migrations.RunSQL(
            "ALTER TABLE internship_period ALTER COLUMN cohort_id SET NOT NULL",
            reverse_sql="ALTER TABLE intership_period ALTER COLUMN cohort_id DROP NOT NULL"
        ),
    ]