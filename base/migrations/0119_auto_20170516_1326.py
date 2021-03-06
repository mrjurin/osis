# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2017-05-16 11:26
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0118_auto_20170516_1153'),
    ]

    operations = [
        migrations.AlterField(
            model_name='learningcomponent',
            name='acronym',
            field=models.CharField(max_length=3),
        ),
        migrations.AlterField(
            model_name='learningcomponentyear',
            name='acronym',
            field=models.CharField(blank=True, max_length=3, null=True),
        ),
        migrations.AlterField(
            model_name='learningcomponentyear',
            name='comment',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='learningcomponentyear',
            name='title',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='learningcomponentyear',
            name='type',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
    ]
