#This file is part galatea module for Tryton.
#The COPYRIGHT file at the top level of this repository contains 
#the full copyright notices and license terms.
from trytond.model import fields
from trytond.pool import PoolMeta

__all__ = ['Party']
__metaclass__ = PoolMeta


class Party:
    __name__ = 'party.party'
    galatea_users = fields.One2Many('galatea.user', 'party', 'Galatea Users')
