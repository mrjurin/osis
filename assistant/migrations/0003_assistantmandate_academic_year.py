# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2016-04-22 13:33
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0031_applicationnotice'),
        ('assistant', '0002_auto_20160419_1520'),
    ]

    operations = [
        migrations.AddField(
            model_name='assistantmandate',
            name='academic_year',
            field=models.ForeignKey(default=2016, on_delete=django.db.models.deletion.CASCADE, to='base.AcademicYear'),
            preserve_default=False,
        ),
    ]