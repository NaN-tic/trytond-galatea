# This file is part galatea module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.model import fields
from trytond.pool import Pool, PoolMeta
from trytond.pyson import Eval


class Party(metaclass=PoolMeta):
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


class Address(metaclass=PoolMeta):
    __name__ = 'party.address'

    _contact_mechanism_states = {
        'readonly': Eval('id', -1) >= 0,
        }

    phone = fields.Function(
        fields.Char("Phone", states=_contact_mechanism_states),
        'get_contact_mechanism', setter='set_contact_mechanism')
    mobile = fields.Function(
        fields.Char("Mobile", states=_contact_mechanism_states),
        'get_contact_mechanism', setter='set_contact_mechanism')
    fax = fields.Function(
        fields.Char("Fax", states=_contact_mechanism_states),
        'get_contact_mechanism', setter='set_contact_mechanism')
    email = fields.Function(
        fields.Char("E-Mail", states=_contact_mechanism_states),
        'get_contact_mechanism', setter='set_contact_mechanism')

    def get_contact_mechanism(self, name):
        for mechanism in self.contact_mechanisms:
            if mechanism.type == name:
                return mechanism.value
        return ''

    @classmethod
    def set_contact_mechanism(cls, addresses, name, value):
        pool = Pool()
        ContactMechanism = pool.get('party.contact_mechanism')

        contact_mechanisms = []
        to_delete = []
        for address in addresses:
            if getattr(address, name):
                for mechanism in address.contact_mechanisms:
                    if mechanism.type == name:
                        break
                if value:
                    mechanism.value = value
                    contact_mechanisms.append(mechanism)
                else:
                    to_delete.append(mechanism)
            elif value:
                contact_mechanisms.append(ContactMechanism(
                        party=address.party,
                        address=address,
                        type=name,
                        value=value))
        ContactMechanism.save(contact_mechanisms)
        ContactMechanism.delete(to_delete)


class PartyReplace(metaclass=PoolMeta):
    __name__ = 'party.replace'

    @classmethod
    def fields_to_replace(cls):
        return super(PartyReplace, cls).fields_to_replace() + [
            ('galatea.user', 'party'),
            ]
