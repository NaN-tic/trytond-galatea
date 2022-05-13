#!/usr/bin/env python
# This file is part galatea module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
import doctest
import unittest
from collections import defaultdict

import trytond.tests.test_tryton
from trytond.model import ModelView, ModelStorage
from trytond.tests.test_tryton import ModuleTestCase, with_transaction
from trytond.tests.test_tryton import doctest_teardown, doctest_checker
from trytond.modules.company.tests import CompanyTestMixin
from trytond.pool import Pool, isregisteredby
from trytond.pyson import Eval, PYSONEncoder


class GalateaCompanyTestMixin(CompanyTestMixin):

    # AssertionError Models "sale.shop" are missing a global rule for field "company"

    @with_transaction()
    def test_company_rule(self):
        "Test missing company rule"
        pool = Pool()
        Rule = pool.get('ir.rule')
        Company = pool.get('company.company')
        Employee = pool.get('company.employee')
        User = pool.get('res.user')

        to_check = defaultdict(set)
        for mname, model in pool.iterobject():
            if mname == 'galatea.website':
                continue
            if (not isregisteredby(model, self.module)
                    or model.__access__
                    or not (issubclass(model, ModelView)
                        and issubclass(model, ModelStorage))
                    or issubclass(model, (Company, Employee, User))):
                continue
            for fname, field in model._fields.items():
                if (field._type == 'many2one'
                        and issubclass(field.get_target(), Company)):
                    to_check[fname].add(mname)

        for fname, models in to_check.items():
            rules = Rule.search([
                    ('rule_group', 'where', [
                            ('model.model', 'in', list(models)),
                            ('global_p', '=', True),
                            ('perm_read', '=', True),
                            ]),
                    ('domain', '=', PYSONEncoder(sort_keys=True).encode(
                            [(fname, 'in', Eval('companies', []))])),
                    ])
            with_rules = {r.rule_group.model.model for r in rules}
            self.assertGreaterEqual(with_rules, models,
                msg='Models "%(models)s" are missing a global rule '
                'for field "%(field)s"' % {
                    'models': ', '.join(models - with_rules),
                    'field': fname,
                    })


class GalateaTestCase(GalateaCompanyTestMixin, ModuleTestCase):
    'Test Galatea module'
    module = 'galatea'


def suite():
    suite = trytond.tests.test_tryton.suite()
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(
        GalateaTestCase))
    suite.addTests(doctest.DocFileSuite('scenario_party_replace.rst',
            tearDown=doctest_teardown, encoding='utf-8',
            optionflags=doctest.REPORT_ONLY_FIRST_FAILURE,
            checker=doctest_checker))
    return suite
