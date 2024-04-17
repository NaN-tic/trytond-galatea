
# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
from trytond.modules.company.tests import CompanyTestMixin
from trytond.tests.test_tryton import ModuleTestCase, with_transaction
from trytond.pool import Pool


class GalateaCompanyTestMixin(CompanyTestMixin):

    @property
    def _skip_company_rule(self):
        return super()._skip_company_rule | {
            ('galatea.website', 'company'),
            }


class GalateaTestCase(GalateaCompanyTestMixin, ModuleTestCase):
    'Test Galatea module'
    module = 'galatea'

    @with_transaction()
    def test_address_contact_mechanisms(self):
        'Party Identifiers'
        pool = Pool()
        Party = pool.get('party.party')
        Address = pool.get('party.address')

        party1, = Party.create([{
                    'name': 'Party 1',
                    }])

        address, = Address.create([{
                    'party': party1.id,
                    'street': 'St sample, 15',
                    'city': 'City',
                    }])
        self.assertTrue(address.id)
        self.assertEqual(address.email, '')
        address.email = 'demo@demo.org'
        address.save()
        self.assertEqual(address.email, 'demo@demo.org')
        self.assertEqual(len(address.contact_mechanisms), 1)
        address.email = 'demo2@demo.org'
        address.save()
        self.assertEqual(address.email, 'demo2@demo.org')
        address.email = None
        address.save()
        self.assertEqual(len(address.contact_mechanisms), 0)

del ModuleTestCase
