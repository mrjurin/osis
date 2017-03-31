# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2017-03-15 13:23
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0097_learningunitcomponent_coefficient_repetition'),
    ]

    operations = [
        migrations.AddField(
            model_name='learningunit',
            name='learning_container',
            field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, to='base.LearningContainer'),
        ),
        migrations.AddField(
            model_name='learningunityear',
            name='status',
            field=models.CharField(blank=True, choices=[('', 'NONE'), ('VALID', 'VALID'), ('INVALID', 'INVALID')], max_length=20, null=True),
        ),
        migrations.AlterField(
            model_name='learningunit',
            name='periodicity',
            field=models.CharField(blank=True, choices=[('ANNUAL', 'ANNUAL'), ('BIENNIAL_EVEN', 'BIENNIAL_EVEN'), ('BIENNIAL_ODD', 'BIENNIAL_ODD')], max_length=20, null=True),
        ),
        migrations.AlterField(
            model_name='learningunityear',
            name='type',
            field=models.CharField(blank=True, choices=[('', 'NONE'), ('COURSE', 'COURSE'), ('MASTER_THESIS', 'MASTER_THESIS'), ('INTERNSHIP', 'INTERNSHIP')], max_length=20, null=True),
        ),
    ]
