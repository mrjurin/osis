# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2017-06-20 08:42
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0135_auto_20170616_0850'),
    ]

    operations = [
        migrations.DeleteModel(
            name='ApplicationNotice',
        ),
        migrations.AlterField(
            model_name='organization',
            name='type',
            field=models.CharField(blank=True, choices=[('MAIN', 'MAIN'), ('ACADEMIC_PARTNER', 'ACADEMIC_PARTNER'), ('INDUSTRIAL_PARTNER', 'INDUSTRIAL_PARTNER'), ('SERVICE_PARTNER', 'SERVICE_PARTNER'), ('COMMERCE_PARTNER', 'COMMERCE_PARTNER'), ('PUBLIC_PARTNER', 'PUBLIC_PARTNER')], default='UNKNOWN', max_length=30, null=True),
        ),
    ]