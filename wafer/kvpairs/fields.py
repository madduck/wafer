# -*- coding: utf-8 -*-
# (c) 2015-16 martin f. krafft <madduck@debconf.org>
# Released under the terms of the same licence as Wafer.

from django.core.exceptions import SuspiciousOperation, ValidationError
try:
    from django.core.exceptions import FieldDoesNotExist
except ImportError:
    # The exception class was not in core but in db.models in Django 1.7
    from django.db.models import FieldDoesNotExist

from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.utils.encoding import python_2_unicode_compatible
from django.db import models
from django.db.models import signals


class ReferencedObjectDescriptor(property):

    def __init__(self, field):
        self.field = field

    def __get__(self, instance, owner):
        if instance is None:
            return self
        if self.field.name not in instance.__dict__:
            raw_data = getattr(instance, self.field.attname)
            instance.__dict__[self.field.name] = self.field.unpack(raw_data)
        return instance.__dict__[self.field.name]

    def __set__(self, instance, value):
        instance.__dict__[self.field.name] = value
        setattr(instance, self.field.attname, self.field.pack(value))


@python_2_unicode_compatible
class RefObjField(models.PositiveIntegerField):

    def __init__(self, ct_path, *args, **kwargs):
        super(RefObjField, self).__init__(*args, **kwargs)
        self.ct_path = ct_path.split('.')
        self.ct_fieldname = self.ct_path.pop()
        self.attname = self.get_attname()

    def __str__(self):
        '''Displays the module, class and name of the field'''
        path = '%s.%s' % (self.__class__.__module__, self.__class__.__name__)
        name = getattr(self, 'name', None)
        fieldpath = getattr(self, 'ct_path', None)
        ret = '<%s' % path
        if fieldpath:
            fieldpath.append(self.ct_fieldname)
            ret = ': '.join((ret, '%s' % '.'.join(fieldpath)))
        if self.ct_pointer:
            ret += '[%s.%s]' % (self.ct_pointer.app_label, self.ct_pointer.model)
        return '>'.join((ret, ''))

    def deconstruct(self):
        name, path, args, kwargs = super(RefObjField, self).deconstruct()
        kwargs['ct_path'] = '.'.join(self.ct_path + [self.ct_fieldname])
        return name, path, args, kwargs

    def pack(self, obj):
        return obj.pk

    def unpack(self, data):
        return self.ct_pointer.get_object_for_this_type(pk=data)

    def get_attname(self):
        return '%s_id' % self.name

    def contribute_to_class(self, cls, name, **kwargs):
        super(RefObjField, self).contribute_to_class(cls, name)
        setattr(cls, name, ReferencedObjectDescriptor(self))

        if not cls._meta.abstract:
            signals.post_init.connect(self.instance_post_init, sender=cls)

    def instance_post_init(self, instance, signal, sender, **kwargs):
        self.is_relation = True
        self.update_ct_pointer(instance)

    def _resolve_ct_instance(self, instance):
        for p in self.ct_path[::-1]:
            instance = getattr(instance, p)
        return getattr(instance, self.ct_fieldname)

    def update_ct_pointer(self, instance):
        self.ct_pointer = self._resolve_ct_instance(instance)
        assert(isinstance(self.ct_pointer, ContentType))
        self.related_model = self.ct_pointer.model_class()

    def get_lookup_constraint(self, constraint_class, alias, targets, sources,
                              lookups, raw_value):
        # cf. django.db.models.fields.related.ForeignObject.get_lookup_constraint
        from django.db.models.sql.where import SubqueryConstraint, AND, OR
        root_constraint = constraint_class()
        assert len(targets) == 1
        assert len(sources) == 1
        lookup_type = lookups[0]

        def get_normalized_value(value):
            try:
                value = (value._get_pk_val(),)
            except AttributeError:
                pass
            return value if isinstance(value, tuple) else (value,)

        if (hasattr(raw_value, '_as_sql') or
                hasattr(raw_value, 'get_compiler')):
            root_constraint.add(SubqueryConstraint(alias, [target.column for target in targets],
                                                   [source.name for source in sources], raw_value),
                                AND)
        elif lookup_type == 'isnull':
            try:
                root_constraint.add(IsNull(targets[0].get_col(alias, sources[0]), raw_value), AND)
            except AttributeError:
                # Django 1.7 does not have get_col
                from django.db.models.sql.datastructures import Col
                root_constraint.add(IsNull(Col(alias, targets[0], sources[0]), raw_value), AND)

        elif lookup_type == 'exact':
            value = get_normalized_value(raw_value)
            for target, source, val in zip(targets, sources, value):
                lookup_class = target.get_lookup(lookup_type)
                try:
                    root_constraint.add(
                        lookup_class(target.get_col(alias, source), val), AND)
                except AttributeError:
                    # Django 1.7 does not have get_col
                    from django.db.models.sql.datastructures import Col
                    root_constraint.add(
                        lookup_class(Col(alias, target, source), val), AND)
        else:
            raise TypeError('%s got invalid lookup: %s' % (self.__class__.__name__, lookup_type))

        return root_constraint
