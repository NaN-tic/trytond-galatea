# This file is part galatea module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
try:
    from trytond.modules.galatea.tests.test_galatea import suite
except ImportError:
    from .test_galatea import suite

__all__ = ['suite']
