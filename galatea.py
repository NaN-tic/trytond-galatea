#This file is part galatea module for Tryton.
#The COPYRIGHT file at the top level of this repository contains 
#the full copyright notices and license terms.
from trytond.model import ModelView, ModelSQL, fields
from trytond.pool import Pool, PoolMeta
from trytond.transaction import Transaction

import pytz
import random
import string

try:
    import hashlib
except ImportError:
    hashlib = None
    import sha

__all__ = ['GalateaWebSite', 'GalateaWebsiteCountry', 'GalateaWebsiteCurrency',
    'GalateaUser', 'GalateaUserWebSite']
__metaclass__ = PoolMeta


class GalateaWebSite(ModelSQL, ModelView):
    'Galatea Web Site'
    __name__ = "galatea.website"
    name = fields.Char('Name', required=True, select=True)
    uri = fields.Char('Uri', required=True,
        help='Base Uri Site (with "/")')
    company = fields.Many2One('company.company', 'Company', required=True)
    active = fields.Boolean('Active')
    registration = fields.Boolean('Registration',
        help='Add website in users when users do a new registration')
    countries = fields.Many2Many(
        'galatea.website-country.country', 'website', 'country',
        'Countries Available')
    currency = fields.Many2One('currency.currency', 'Currency', required=True)
    timezone = fields.Selection(
        [(x, x) for x in pytz.common_timezones], 'Timezone', translate=False
        )
    smtp_server = fields.Many2One('smtp.server', 'SMTP Server',
        domain=[('state', '=', 'done')], required=True)

    @staticmethod
    def default_timezone():
        return 'UTC'

    @staticmethod
    def default_active():
        return True

    @staticmethod
    def default_registration():
        return True

    @staticmethod
    def default_company():
        return Transaction().context.get('company')

    @classmethod
    def __setup__(cls):
        super(GalateaWebSite, cls).__setup__()
        cls._sql_constraints = [
            ('name_uniq', 'UNIQUE(name)',
             'Another site with the same name already exists!')
        ]


class GalateaWebsiteCountry(ModelSQL):
    "Website Country Relations"
    __name__ = 'galatea.website-country.country'
    website = fields.Many2One('galatea.website', 'Website')
    country = fields.Many2One('country.country', 'Country')


class GalateaWebsiteCurrency(ModelSQL):
    "Currencies to be made available on website"
    __name__ = 'galatea.website-currency.currency'
    _table = 'website_currency_rel'
    website = fields.Many2One(
        'galatea.website', 'Website',
        ondelete='CASCADE', select=1, required=True)
    currency = fields.Many2One(
        'currency.currency', 'Currency',
        ondelete='CASCADE', select=1, required=True)


class GalateaUser(ModelSQL, ModelView):
    """Galatea Users"""
    __name__ = "galatea.user"
    _rec_name = 'display_name'

    party = fields.Many2One('party.party', 'Party', required=True,
        ondelete='CASCADE')
    display_name = fields.Char('Display Name', required=True)
    email = fields.Char("e-Mail", required=True)
    password = fields.Char('Password')
    salt = fields.Char('Salt', size=8)
    activation_code = fields.Char('Unique Activation Code')
    company = fields.Many2One('company.company', 'Company', required=True)
    timezone = fields.Selection(
        [(x, x) for x in pytz.common_timezones], 'Timezone', translate=False
        )
    manager = fields.Boolean('Manager', help='Allow user in manager sections')
    active = fields.Boolean('Active', help='Allow login users')
    websites = fields.Many2Many('galatea.user-galatea.website', 
        'user', 'website', 'Websites',
        help='Users will be available this websites to login')

    @staticmethod
    def default_timezone():
        return "UTC"

    @staticmethod
    def default_active():
        return True

    @staticmethod
    def default_company():
        return Transaction().context.get('company')

    @staticmethod
    def default_websites():
        Website = Pool().get('galatea.website')
        return [p.id for p in Website.search([('registration','=',True)])]

    @classmethod
    def __setup__(cls):
        super(GalateaUser, cls).__setup__()
        cls._sql_constraints += [
            ('unique_email_company', 'UNIQUE(email, company)',
                'Email must be unique in a company'),
        ]

    @staticmethod
    def _convert_values(values):
        """
        A helper method which looks if the password is specified in the values.
        If it is, then the salt is also made and added

        :param values: A dictionary of field: value pairs
        """
        if values.get('password'):
            values['salt'] = ''.join(random.sample(
                string.ascii_letters + string.digits, 8))
            password = values['password'] + values['salt']
            if hashlib:
                digest = hashlib.sha1(password).hexdigest()
            else:
                digest = sha.new(password).hexdigest()
            values['password'] = digest

        return values

    @classmethod
    def create(cls, vlist):
        "Add salt before saving"
        vlist = [cls._convert_values(vals.copy()) for vals in vlist]
        return super(GalateaUser, cls).create(vlist)

    @classmethod
    def write(cls, users, values):
        "Update salt before saving"
        return super(GalateaUser, cls).write(users, cls._convert_values(values))


class GalateaUserWebSite(ModelSQL):
    'Galatea User - Website'
    __name__ = 'galatea.user-galatea.website'
    _table = 'galatea_user_galatea_website'
    user = fields.Many2One('galatea.user', 'User', ondelete='CASCADE',
            select=True, required=True)
    website = fields.Many2One('galatea.website', 'Website', ondelete='RESTRICT',
            select=True, required=True)
