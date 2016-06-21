# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2016-04-13 09:37
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0030_auto_20160413_1249'),
    ]

    operations = [
        migrations.CreateModel(
            name='ApplicationNotice',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('subject', models.CharField(max_length=255)),
                ('notice', models.TextField()),
                ('start_publish', models.DateTimeField()),
                ('stop_publish', models.DateTimeField()),
            ],
        ),
    ]