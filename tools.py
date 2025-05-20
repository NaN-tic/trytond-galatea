# This file is part galatea module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.tools import slugify

def slugify_file(value):
    """Convert attachment name to slug: az09 and replace spaces by -"""
    fname = value.lower().split('.')
    fn = fname[0]
    name = slugify(fn)

    if len(fname) > 1:
        return '%s.%s' % (name, fname[1])
    else:
        return name


def remove_special_chars(text):
    """Remove some specials chars from text:
        - Blanks (\s)
        - New lines (\n or \r)
        - Tab (\t)
    """
    if text is None:
        return ''
    return text.replace(r' ', '').replace(r'\n', '').replace(r'\r', '').replace(r'\t', '')
