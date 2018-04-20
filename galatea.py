# This file is part galatea module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.model import ModelView, ModelSQL, fields, Unique
from trytond.wizard import Wizard, StateTransition, StateView, Button
from trytond.pool import Pool
from trytond.transaction import Transaction
from trytond.sendmail import SMTPDataManager, sendmail_transactional
from trytond.config import config
from email import Utils
from email.header import Header
from email.mime.text import MIMEText
from fabric.api import env as fenv, sudo as fsudo
from fabric.contrib.files import exists as fexists
from flask_login import UserMixin
import pytz
import random
import string

try:
    import hashlib
except ImportError:
    hashlib = None
    import sha

__all__ = ['GalateaWebSite', 'GalateaWebsiteCountry', 'GalateaWebsiteLang',
    'GalateaWebsiteCurrency', 'GalateaUser', 'GalateaUserWebSite',
    'GalateaRemoveCacheStart', 'GalateaRemoveCache',
    'GalateaSendPasswordStart', 'GalateaSendPasswordResult',
    'GalateaSendPassword']


class GalateaWebSite(ModelSQL, ModelView):
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
    active = fields.Boolean('Active')
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
            help='Almost all search engines recommend it to be shorter ' \
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
        cls._error_messages.update({
                'smtp_error': 'Wrong connection to SMTP server. '
                        'Not send email.',
                })
        cls._buttons.update({
                'remove_cache': {},
                })

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

    @staticmethod
    def send_email(server, recipients, subject, body):
        from_ = server.smtp_email
        if server.smtp_use_email:
            from_ = server.smtp_email

        msg = MIMEText(body, _charset='utf-8')
        msg['Subject'] = Header(subject, 'utf-8')
        msg['From'] = from_
        msg['To'] = ', '.join(recipients)
        msg['Reply-to'] = server.smtp_email
        # msg['Date']     = Utils.formatdate(localtime = 1)
        msg['Message-ID'] = Utils.make_msgid()

        datamanager = SMTPDataManager()
        datamanager._server = server.get_smtp_server()
        sendmail_transactional(from_, recipients, msg, datamanager=datamanager)

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


class GalateaUser(ModelSQL, ModelView, UserMixin):
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
    company = fields.Many2One('company.company', 'Company', required=True)
    timezone = fields.Selection(
        [(x, x) for x in pytz.common_timezones], 'Timezone', translate=False
        )
    manager = fields.Boolean('Manager', help='Allow user in manager sections')
    active = fields.Boolean('Active', help='Allow login users')
    websites = fields.Many2Many('galatea.user-galatea.website', 
        'user', 'website', 'Websites',
        help='Users will be available in those websites to login')

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
        t = cls.__table__()
        cls._sql_constraints += [
            ('unique_email_company', Unique(t, t.email, t.company),
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
            password = values['password']
            if isinstance(password, unicode):
                password = password.encode('utf-8')
            password += values['salt']
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

    @classmethod
    def signal_login(cls, user, session=None, website=None):
        "Flask signal to login"
        return

    @classmethod
    def signal_logout(cls, user, session=None, website=None):
        "Flask signal to logout"
        return

    @classmethod
    def signal_registration(cls, user, data=None, website=None):
        "Flask signal to registration"
        return

    @classmethod
    def _get_user_domain(cls, website, request):
        return [
            ('email', '=', request.form.get('email')),
            ('active', '=', True),
            ('websites', 'in', [website]),
            ]

    @classmethod
    def get_user(cls, website, request):
        return cls.search(cls._get_user_domain(website, request), limit=1)


class GalateaUserWebSite(ModelSQL):
    'Galatea User - Website'
    __name__ = 'galatea.user-galatea.website'
    _table = 'galatea_user_galatea_website'
    user = fields.Many2One('galatea.user', 'User', ondelete='CASCADE',
            select=True, required=True)
    website = fields.Many2One('galatea.website', 'Website', ondelete='RESTRICT',
            select=True, required=True)


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

    @classmethod
    def __setup__(cls):
        super(GalateaRemoveCache, cls).__setup__()
        cls._error_messages.update({
            'not_dir_exist': 'Directory "%s" not exist.',
        })

    def transition_remove(self):
        pool = Pool()
        Website = pool.get('galatea.website')

        fenv.host_string = config.get('galatea', 'host')
        fenv.password = config.get('galatea', 'password')

        websites = Website.browse(Transaction().context['active_ids'])

        for website in websites:
            cache_directories = Website.cache_directories(website)
            for directory in cache_directories:
                if fexists(directory, use_sudo=True):
                    fsudo("rm -rf %s/*" % directory)
                else:
                    self.raise_user_error('not_dir_exist', directory)
        return 'end'


class GalateaSendPasswordStart(ModelView):
    'Galatea Send Start'
    __name__ = 'galatea.send.password.start'
    password = fields.Char('Password', required=True)
    website = fields.Many2One('galatea.website', 'Website', required=True,
        help='Select a website to send email (STMP server).')

    @classmethod
    def default_website(cls):
        Website = Pool().get('galatea.website')
        websites = Website.search([('active', '=', True)])
        if len(websites) >= 1:
            return websites[0].id


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
        cls._error_messages.update({
                'send_info': 'Send new password to %s',
                'email_subject': '%s. New password reset',
                'email_text': 'Hello %s\n' \
                    'New password reset for your user account %s: %s\n\n' \
                    '%s\n\n' \
                    'You could drop this email.\n' \
                    'Don\'t repply this email. It\'s was generated automatically'
                })

    def transition_send(self):
        pool = Pool()
        Website = pool.get('galatea.website')
        User = pool.get('res.user')
        GalateaUser = pool.get('galatea.user')

        password = self.start.password
        website = self.start.website

        users = GalateaUser.browse(Transaction().context['active_ids'])

        for user in users:
            recipients = [user.email]
            sites = []
            for site in user.websites:
                sites.append(site.uri)
            if user.party.lang:
                lang = user.party.lang.code
            else:
                lang = User(Transaction().user).language.code
            with Transaction().set_context(language=lang):
                subject = self.raise_user_error('email_subject',
                    (website.name),
                    raise_exception=False)
                body = self.raise_user_error('email_text',
                    (user.display_name, user.email, password, "\n".join(sites)),
                    raise_exception=False)

            Website.send_email(website.smtp_server, recipients, subject, body)

        GalateaUser.write(users, {'password': password})

        self.result.info = self.raise_user_error('send_info',
                (','.join(str(u.email) for u in users)),
                raise_exception=False)
        return 'result'

    def default_result(self, fields):
        info_ = self.result.info
        return {
            'info': info_,
            }
