# -*- coding: utf-8 -*-
# Generated by Django 1.11.11 on 2018-04-14 21:20
from __future__ import unicode_literals

from django.db import migrations
import django.db.models.manager


class Migration(migrations.Migration):

    dependencies = [
        ('services', '0038_auto_20180412_0822'),
    ]

    operations = [
        migrations.AlterModelManagers(
            name='service',
            managers=[
                ('objects', django.db.models.manager.Manager()),
                ('base_objects', django.db.models.manager.Manager()),
            ],
        ),
    ]
