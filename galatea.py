# This file is part galatea module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.config import config
from trytond.model import ModelView, ModelSQL, DeactivableMixin, fields, Unique
from trytond.wizard import Wizard, StateTransition, StateView, Button
from trytond.pool import Pool
from trytond.pyson import Eval
from trytond.transaction import Transaction
from trytond.sendmail import sendmail_transactional
from trytond.i18n import gettext
from trytond.exceptions import UserError
from trytond import backend
from .tools import remove_special_chars
from datetime import datetime
from email.utils import make_msgid
from email.header import Header
from email.mime.text import MIMEText
from flask_login import UserMixin
import subprocess
import logging
import pytz
import random
import string
import os
import hashlib
import secrets

logger = logging.getLogger(__name__)

__all__ = ['GalateaWebSite', 'GalateaWebsiteCountry', 'GalateaWebsiteLang',
    'GalateaWebsiteCurrency', 'GalateaUser', 'GalateaUserWebSite',
    'GalateaRemoveCacheStart', 'GalateaRemoveCache',
    'GalateaSendPasswordStart', 'GalateaSendPasswordResult',
    'GalateaSendPassword']


class GalateaWebSite(DeactivableMixin, ModelSQL, ModelView):
    'Galatea Web Site'
    __name__ = "galatea.website"
    name = fields.Char('Name', required=True, select=True)
    uri = fields.Char('Uri', required=True,
        help='Base Uri Site (with "/")')
    folder = fields.Char('Folder', required=True,
        help='Flask App directory')
    static_folder = fields.Char('Static Folder', required=True,
        help='Flask Static directory')
    company = fields.Many2One('company.company', 'Company', required=True)
    registration = fields.Boolean('Registration',
        help='Add website in users when users do a new registration')
    country = fields.Many2One('country.country', 'Country', required=True,
        help='Default Country')
    countries = fields.Many2Many('galatea.website-country.country',
        'website', 'country', 'Countries')
    languages = fields.Many2Many('galatea.website-ir.lang',
        'website', 'language', 'Languages')
    currency = fields.Many2One('currency.currency', 'Currency', required=True)
    timezone = fields.Selection(
        [(x, x) for x in pytz.common_timezones], 'Timezone', translate=False
        )
    smtp_server = fields.Many2One('smtp.server', 'SMTP Server',
        domain=[('state', '=', 'done')], required=True)
    metadescription = fields.Char('Meta Description', translate=True,
        help='Almost all search engines recommend it to be shorter '
        'than 155 characters of plain text')
    metakeyword = fields.Char('Meta Keyword', translate=True)
    metatitle = fields.Char('Meta Title', translate=True)
    logo = fields.Char('Logo')

    @classmethod
    def __setup__(cls):
        super(GalateaWebSite, cls).__setup__()
        t = cls.__table__()
        cls._sql_constraints = [
            ('name_uniq', Unique(t, t.name),
                'Another site with the same name already exists!')
            ]
        cls._buttons.update({
                'remove_cache': {},
                })

    @staticmethod
    def default_timezone():
        return 'UTC'

    @staticmethod
    def default_registration():
        return True

    @staticmethod
    def default_company():
        return Transaction().context.get('company')

    @staticmethod
    def send_email(server, recipients, subject, body):
        from_cfg = config.get('email', 'from')

        msg = MIMEText(body, _charset='utf-8')
        msg['Subject'] = Header(subject, 'utf-8')
        msg['From'] = from_cfg
        msg['To'] = ', '.join(recipients)
        msg['Reply-to'] = server.smtp_email
        msg['Message-ID'] = make_msgid()

        sendmail_transactional(from_cfg, recipients, msg)

    @classmethod
    def cache_directories(cls, website):
        directories = []
        directories.append('%s/media/cache' % (website.folder))
        return directories

    @classmethod
    @ModelView.button_action('galatea.wizard_galatea_remove_cache')
    def remove_cache(cls, websites):
        pass


class GalateaWebsiteCountry(ModelSQL):
    "Website Country Relations"
    __name__ = 'galatea.website-country.country'
    website = fields.Many2One('galatea.website', 'Website')
    country = fields.Many2One('country.country', 'Country')


class GalateaWebsiteLang(ModelSQL):
    "Website Language Relations"
    __name__ = 'galatea.website-ir.lang'
    website = fields.Many2One('galatea.website', 'Website')
    language = fields.Many2One('ir.lang', 'Language')


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


class GalateaUserMixin(UserMixin):
    __no_slots__ = True


class GalateaUser(DeactivableMixin, GalateaUserMixin, ModelSQL, ModelView):
    """Galatea Users"""
    __name__ = "galatea.user"
    _rec_name = 'display_name'

    party = fields.Many2One('party.party', 'Party', required=True,
        ondelete='CASCADE')
    display_name = fields.Char('Display Name', required=True)
    email = fields.Char("e-Mail", required=True)
    password = fields.Char('Password', required=True)
    salt = fields.Char('Salt', size=8)
    activation_code = fields.Char('Unique Activation Code')
    timezone = fields.Selection(
        [(x, x) for x in pytz.common_timezones], 'Timezone', translate=False
        )
    manager = fields.Boolean('Manager', help='Allow user in manager sections')
    websites = fields.Many2Many('galatea.user-galatea.website',
        'user', 'website', 'Websites',
        help='Users will be available in those websites to login')
    login_expire = fields.DateTime('Login Expire')
    last_login = fields.DateTime('Last Login', readonly=True)

    @staticmethod
    def default_timezone():
        return "UTC"

    @staticmethod
    def default_websites():
        Website = Pool().get('galatea.website')
        return [p.id for p in Website.search([('registration', '=', True)])]

    @classmethod
    def __setup__(cls):
        super(GalateaUser, cls).__setup__()
        t = cls.__table__()
        cls._sql_constraints += [
            ('unique_email_company', Unique(t, t.email),
                'Email must be unique'),
            ]
        cls._buttons.update({
                'activate': {
                    'invisible': ~Eval('activation_code'),
                    'depends': ['activation_code'],
                    },
                })

    @classmethod
    def __register__(cls, module_name):
        table = cls.__table_handler__(module_name)

        # Migration from 5.4: drop company column
        if table.column_exist('company'):
            table.drop_constraint('unique_email_company')
            table.drop_column('company')

        super(GalateaUser, cls).__register__(module_name)

    @classmethod
    @ModelView.button
    def activate(cls, users):
        active_users = [user for user in users if user.activation_code]
        cls.write(active_users, {'activation_code': None})

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
            password = values['password']
            password = str(password.encode('utf-8'), 'utf-8')
            password += values['salt']
            digest = hashlib.sha1(password.encode('utf-8')).hexdigest()
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
        values = cls._convert_values(values)
        return super(GalateaUser, cls).write(users, values)

    @classmethod
    def search_rec_name(cls, name, clause):
        domain = super(GalateaUser, cls).search_rec_name(name, clause)
        if clause[1].startswith('!') or clause[1].startswith('not '):
            bool_op = 'AND'
        else:
            bool_op = 'OR'
        return [bool_op,
            domain,
            ('email',) + tuple(clause[1:]),
            ('party.name',) + tuple(clause[1:]),
            ('party.addresses.street',) + tuple(clause[1:]),
            ('party.addresses.postal_code',) + tuple(clause[1:]),
            ('party.addresses.city',) + tuple(clause[1:]),
            ('party.addresses.subdivision.name',) + tuple(clause[1:]),
            ('party.contact_mechanisms.value',) + tuple(clause[1:]),
            ]

    @classmethod
    def signal_login(cls, user, session=None, website=None):
        "Flask signal to login"
        DatabaseOperationalError = backend.DatabaseOperationalError

        user_id = user.id
        try:
            with Transaction().new_transaction(autocommit=True):
                User = Pool().get('galatea.user')
                galatea_user = User(user_id)
                if galatea_user.activation_code:
                    # keep activation_code in case user forget the password,
                    # and not show current_password input in new-password form
                    if len(galatea_user.activation_code) == 12:
                        galatea_user.password = galatea_user.activation_code
                    else:
                        galatea_user.activation_code = None
                galatea_user.last_login = datetime.now()
                galatea_user.save()
        except DatabaseOperationalError:
            logger.debug('Galatea user last login failed', exc_info=True)

    @classmethod
    def signal_logout(cls, user, session=None, website=None):
        "Flask signal to logout"
        pass

    @classmethod
    def signal_registration(cls, user, data=None, website=None):
        "Flask signal to registration"
        pass

    @classmethod
    def _get_user_domain(cls, website, request):
        email = remove_special_chars(request.authorization
            and request.authorization.username or request.form.get('email'))
        return [
            ('email', '=', email),
            ('active', '=', True),
            ('websites', 'in', [website]),
            ]

    @classmethod
    def get_user(cls, website, request):
        domain = cls._get_user_domain(website, request)
        return cls.search(domain, limit=1)

    @classmethod
    def random_password(cls):
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for i in range(20))

    @classmethod
    def reset_password(cls, users, send_email=True):
        pool = Pool()
        Website = pool.get('galatea.website')
        User = pool.get('res.user')
        GalateaUser = pool.get('galatea.user')

        to_write = []
        for user in users:
            password = cls.random_password()
            recipients = [user.email]

            if not user.websites:
                raise UserError(gettext('galatea.msg_missing_user_site',
                    user=user.rec_name))

            if user.party.lang:
                lang = user.party.lang.code
            else:
                ruser = User(Transaction().user)
                lang = ruser.language and ruser.language.code or 'en'

            with Transaction().set_context(language=lang):
                subject = gettext('galatea.email_subject',
                    website=" ".join([w.name for w in user.websites]))
                body = gettext('galatea.email_text',
                    name=user.display_name,
                    email=user.email,
                    password=password,
                    websites="\n".join([w.uri for w in user.websites]))

            if send_email and user.websites:
                smtp_server = user.websites[0].smtp_server
                Website.send_email(smtp_server, recipients, subject, body)

            to_write.extend(([user], {'password': password}))

        if to_write:
            GalateaUser.write(*to_write)


class GalateaUserWebSite(ModelSQL):
    'Galatea User - Website'
    __name__ = 'galatea.user-galatea.website'
    _table = 'galatea_user_galatea_website'
    user = fields.Many2One('galatea.user', 'User', ondelete='CASCADE',
            select=True, required=True)
    website = fields.Many2One(
        'galatea.website', 'Website',
        ondelete='RESTRICT', select=True, required=True)

    @classmethod
    def __setup__(cls):
        super().__setup__()
        cls.__access__.add('website')


class GalateaRemoveCacheStart(ModelView):
    'Galatea Remove Cache Start'
    __name__ = 'galatea.remove.cache.start'


class GalateaRemoveCache(Wizard):
    'Galatea Remove Cache'
    __name__ = "galatea.remove.cache"
    start = StateView('galatea.remove.cache.start',
        'galatea.galatea_remove_cache_start', [
            Button('Cancel', 'end', 'tryton-cancel'),
            Button('Remove', 'remove', 'tryton-ok', default=True),
            ])
    remove = StateTransition()

    def transition_remove(self):
        pool = Pool()
        Website = pool.get('galatea.website')

        websites = Website.browse(Transaction().context['active_ids'])

        for website in websites:
            cache_directories = Website.cache_directories(website)
            for directory in cache_directories:
                if os.path.exists(directory):
                    process = subprocess.Popen(
                        'rm -rf %s/*' % directory, shell=True)
                    output, err = process.communicate()
                else:
                    raise UserError(gettext('galatea.not_dir_exist',
                        directory=directory))
        return 'end'


class GalateaSendPasswordStart(ModelView):
    'Galatea Send Start'
    __name__ = 'galatea.send.password.start'


class GalateaSendPasswordResult(ModelView):
    'Galatea Send Result'
    __name__ = 'galatea.send.password.result'
    info = fields.Text('Info', readonly=True)


class GalateaSendPassword(Wizard):
    'Send Password by email'
    __name__ = "galatea.send.password"
    start = StateView('galatea.send.password.start',
        'galatea.galatea_send_password_start', [
            Button('Cancel', 'end', 'tryton-cancel'),
            Button('Send', 'send', 'tryton-ok', default=True),
            ])
    send = StateTransition()
    result = StateView('galatea.send.password.result',
        'galatea.galatea_send_password_result', [
            Button('Close', 'end', 'tryton-close'),
            ])

    @classmethod
    def __setup__(cls):
        super(GalateaSendPassword, cls).__setup__()

    def transition_send(self):
        GalateaUser = Pool().get('galatea.user')

        users = GalateaUser.browse(Transaction().context['active_ids'])

        GalateaUser.reset_password(users)

        self.result.info = gettext('galatea.send_info',
                email=','.join(str(u.email) for u in users))
        return 'result'

    def default_result(self, fields):
        info_ = self.result.info
        return {
            'info': info_,
            }
