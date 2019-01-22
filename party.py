# This file is part galatea module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.model import fields
from trytond.pool import PoolMeta

__all__ = ['Party', 'PartyReplace']


class Party:
    __metaclass__ = PoolMeta
    __name__ = 'party.party'
    galatea_users = fields.One2Many('galatea.user', 'party', 'Galatea Users')

    @classmethod
    def copy(cls, parties, default=None):
        if default is None:
            default = {}
        else:
            default = default.copy()
        default.setdefault('galatea_users', None)
        return super(Party, cls).copy(parties, default=default)


class PartyReplace:
    __metaclass__ = PoolMeta
    __name__ = 'party.replace'

    @classmethod
    def fields_to_replace(cls):
        return super(PartyReplace, cls).fields_to_replace() + [
            ('galatea.user', 'party'),
            ]
