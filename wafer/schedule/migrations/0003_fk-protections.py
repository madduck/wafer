# -*- coding: utf-8 -*-
# Generated by Django 1.9.2.dev20160114123008 on 2016-01-15 03:48
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('schedule', '0002_auto_20140909_1403'),
    ]

    operations = [
        migrations.AlterField(
            model_name='scheduleitem',
            name='venue',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='schedule.Venue'),
        ),
        migrations.AlterField(
            model_name='slot',
            name='day',
            field=models.ForeignKey(blank=True, help_text='Day for this slot', null=True, on_delete=django.db.models.deletion.PROTECT, to='schedule.Day'),
        ),
    ]