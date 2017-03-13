# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-03-13 19:24
from __future__ import unicode_literals

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uwnetid', models.SlugField(max_length=16, unique=True)),
                ('uwregid', models.CharField(db_index=True, max_length=32, null=True, unique=True)),
                ('last_visit', models.DateTimeField(default=datetime.datetime(2017, 3, 13, 19, 24, 55, 158944))),
            ],
        ),
    ]
