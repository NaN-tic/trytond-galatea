======================
Party Replace Scenario
======================

Imports::

    >>> from proteus import Model, Wizard
    >>> from trytond.tests.tools import activate_modules
    >>> from trytond.modules.company.tests.tools import create_company, \
    ...     get_company

Install activity::

    >>> config = activate_modules('galatea')

Create company::

    >>> _ = create_company()
    >>> company = get_company()

Create parties::

    >>> Party = Model.get('party.party')
    >>> party = Party(name='Customer')
    >>> party.save()
    >>> party2 = Party(name='Customer')
    >>> party2.save()

Create a User::

    >>> GalateaUser = Model.get('galatea.user')
    >>> user = GalateaUser()
    >>> user.party = party
    >>> user.display_name = 'Customer'
    >>> user.email = 'email@domain.com'
    >>> user.password = '123456'
    >>> user.save()

Try replace active party::

    >>> replace = Wizard('party.replace', models=[party])
    >>> replace.form.source = party
    >>> replace.form.destination = party2
    >>> replace.execute('replace')

Check fields have been replaced::

    >>> user.reload()
    >>> user.party == party2
    True
