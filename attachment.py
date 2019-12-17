# This file is part galatea module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.pool import PoolMeta
from trytond.model import fields
from .tools import slugify

__all__ = ['Attachment']


class Attachment(metaclass=PoolMeta):
    __name__ = 'ir.attachment'
    allow_galatea = fields.Boolean('Allow Galatea', select=True)

    @fields.depends('allow_galatea', 'name')
    def on_change_name(self):
        if self.allow_galatea and self.name:
            first, dot, second = self.name.rpartition('.')
            self.name = slugify(first) + dot + slugify(second)

    @fields.depends('allow_galatea', 'name')
    def on_change_allow_galatea(self):
        if self.allow_galatea and self.name:
            first, dot, second = self.name.rpartition('.')
            self.name = slugify(first) + dot + slugify(second)

    @classmethod
    def create(cls, vlist):
        for values in vlist:
            values = values.copy()
            if values.get('allow_galatea'):
                slug = slugify(values.get('name'))
                values['name'] = slug
        return super(Attachment, cls).create(vlist)
