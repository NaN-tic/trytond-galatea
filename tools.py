# This file is part galatea module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
import logging

try:
    import slug
except ImportError:
    logging.getLogger('galatea').error(
        'Unable to import slug. Install slug package.')


def slugify(value):
    """Convert value to slug: az09 and replace spaces by -"""
    if not slug:
        name = ''
    else:
        if isinstance(value, unicode):
            name = slug.slug(value)
        else:
            name = slug.slug(unicode(value, 'UTF-8'))
    return name


def slugify_file(value):
    """Convert attachment name to slug: az09 and replace spaces by -"""
    if not slug:
        return value
    fname = value.lower().split('.')
    fn = fname[0]
    if isinstance(fn, unicode):
        name = slug.slug(fn)
    else:
        name = slug.slug(unicode(fn, 'UTF-8'))

    if len(fname) > 1:
        return '%s.%s' % (name, fname[1])
    else:
        return name
