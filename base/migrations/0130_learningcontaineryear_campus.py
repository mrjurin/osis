# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2017-06-02 09:53
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0129_auto_20170601_1542'),
    ]

    operations = [
        migrations.AddField(
            model_name='learningcontaineryear',
            name='campus',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='base.Campus'),
        ),
    ]
