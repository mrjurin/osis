# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2016-07-04 20:59
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('internship', '0016_intenshipstudentinformations'),
    ]

    operations = [
        migrations.AlterField(
            model_name='internshipstudentinformation',
            name='phone_mobile',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
