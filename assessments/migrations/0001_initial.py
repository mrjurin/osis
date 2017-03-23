# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2017-03-23 09:14
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='ScoresEncoding',
            fields=[
                ('id', models.BigIntegerField(primary_key=True, serialize=False)),
                ('total_exam_enrollments', models.IntegerField()),
                ('exam_enrollments_encoded', models.IntegerField()),
                ('scores_not_yet_submitted', models.IntegerField()),
                ('enrollment_state', models.CharField(choices=[('ENROLLED', 'ENROLLED'), ('NOT_ENROLLED', 'NOT_ENROLLED')], default='ENROLLED', max_length=20)),
            ],
            options={
                'db_table': 'app_scores_encoding',
                'permissions': (('can_access_scoreencoding', 'Can access scoreencoding'),),
                'managed': False,
            },
        ),
    ]