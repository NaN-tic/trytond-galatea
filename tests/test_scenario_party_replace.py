import unittest

from proteus import Model, Wizard
from trytond.modules.company.tests.tools import create_company
from trytond.tests.test_tryton import drop_db
from trytond.tests.tools import activate_modules


class Test(unittest.TestCase):

    def setUp(self):
        drop_db()
        super().setUp()

    def tearDown(self):
        drop_db()
        super().tearDown()

    def test(self):

        # Install activity
        activate_modules('galatea')

        # Create company
        _ = create_company()

        # Create parties
        Party = Model.get('party.party')
        party = Party(name='Customer')
        party.save()
        party2 = Party(name='Customer')
        party2.save()

        # Create a User
        GalateaUser = Model.get('galatea.user')
        user = GalateaUser()
        user.party = party
        user.display_name = 'Customer'
        user.email = 'email@domain.com'
        user.password = '123456'
        user.save()

        # Try replace active party
        replace = Wizard('party.replace', models=[party])
        replace.form.source = party
        replace.form.destination = party2
        replace.execute('replace')

        # Check fields have been replaced
        user.reload()
        self.assertEqual(user.party, party2)
