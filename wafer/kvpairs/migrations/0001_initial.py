# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings
import wafer.kvpairs.fields


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('auth', '0006_require_contenttypes_0002'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Key',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255, verbose_name=b'Key name')),
                ('group', models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, verbose_name=b'Key owner group', to='auth.Group', null=True)),
                ('model_ct', models.ForeignKey(verbose_name=b'Referenced model type', to='contenttypes.ContentType')),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, verbose_name=b'Key owner', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Key',
            },
        ),
        migrations.CreateModel(
            name='KeyValuePair',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('ref_obj', wafer.kvpairs.fields.RefObjField(ct_path=b'key.model_ct')),
                ('value', models.CharField(max_length=65535, verbose_name=b'Value for key associated with model instance')),
                ('key', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, verbose_name=b'Base key context', to='kvpairs.Key')),
            ],
            options={
                'verbose_name': 'Key-value pair',
            },
        ),
        migrations.AlterUniqueTogether(
            name='keyvaluepair',
            unique_together=set([('key', 'ref_obj')]),
        ),
        migrations.AlterUniqueTogether(
            name='key',
            unique_together=set([('model_ct', 'name')]),
        ),
    ]
