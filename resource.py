# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.model import ModelSQL, ModelView, fields
from trytond.pool import Pool
from trytond.pyson import Bool, If, Eval
from trytond.transaction import Transaction

from .tools import slugify

__all__ = ['GalateaTemplate', 'GalateaTemplateModel',
    'GalateaUri']


class GalateaTemplate(ModelSQL, ModelView):
    '''Galatea Template'''
    __name__ = 'galatea.template'
    _rec_name = 'filename'

    filename = fields.Char('Filename', required=True)
    # TODO: available = fields.Function(fields.Boolean())
    # TODO: path, theme or something to could have "collections" of templates
    allowed_models = fields.Many2Many('galatea.template-ir.model', 'template',
        'model', 'Allowed Models',
        help="The models compatible with this template, which instances can "
        "be associated with an uri that use this template.")

    @classmethod
    def __setup__(cls):
        super(GalateaTemplate, cls).__setup__()
        cls._sql_constraints += [
            ('filename_uniq', 'UNIQUE (filename)',
                'The file name of the Galatea Template must be unique.'),
            ]


class GalateaTemplateModel(ModelSQL):
    'Galatea Template - Model'
    __name__ = 'galatea.template-ir.model'
    template = fields.Many2One('galatea.template', 'Galatea Template',
        ondelete='CASCADE', required=True, select=True)
    model = fields.Many2One('ir.model', 'Model', ondelete='CASCADE',
        required=True, select=True)


class GalateaUri(ModelSQL, ModelView):
    '''Galatea Uri'''
    __name__ = 'galatea.uri'
    _rec_name = 'uri'

    website = fields.Many2One('galatea.website', 'Website', required=True,
        select=True, ondelete='CASCADE')
    name = fields.Char('Name', translate=True, required=True)
    slug = fields.Char('Slug', translate=True, required=True, select=True)
    parent = fields.Many2One('galatea.uri', 'Parent', select=True, domain=[
            ('website', '=', Eval('website')),
            ], depends=['website'])
    left = fields.Integer('Left', required=True, select=True)
    right = fields.Integer('Right', required=True, select=True)
    childs = fields.One2Many('galatea.uri', 'parent', 'Children')
    sequence = fields.Integer('Sequence')
    uri = fields.Function(fields.Char('URI'),
        'get_uri', searcher='search_uri')
    type = fields.Selection([
            ('content', 'Content'),
            ('internal_redirection', 'Internal Redirection'),
            ('external_redirection', 'External Redirection'),
            ], 'Type', required=True)
    template = fields.Many2One('galatea.template', 'Template', domain=[
            If(Bool(Eval('content_model')),
                ('allowed_models', 'in', [Eval('content_model')]),
                ()),
            ],
        states={
            'invisible': Eval('type') != 'content',
            'required': Eval('type') == 'content',
            }, depends=['content_model', 'type'])
    content = fields.Reference('Content', selection='get_content_types',
            selection_change_with=['template'], select=True, states={
            'invisible': Eval('type') != 'content',
            }, depends=['website', 'type'])
    content_model = fields.Function(fields.Many2One('ir.model',
            'Content Model'),
        'on_change_with_content_model')
    internal_redirection = fields.Many2One('galatea.uri',
        'Internal Redirection', states={
            'invisible': Eval('type') != 'internal_redirection',
            'required': Eval('type') == 'internal_redirection',
            }, depends=['type'])
    external_redirection = fields.Char('External Redirection', states={
            'invisible': Eval('type') != 'external_redirection',
            'required': Eval('type') == 'external_redirection',
            }, depends=['type'])
    menus = fields.One2Many('galatea.cms.menu', 'target_uri', 'Menus',
            readonly=True)
    active = fields.Boolean('Active', select=True)

    @classmethod
    def __setup__(cls):
        super(GalateaUri, cls).__setup__()
        cls._order.insert(0, ('sequence', 'ASC'))
        cls._order.insert(1, ('id', 'ASC'))
        cls._sql_constraints += [
            ('uri_uniq', 'UNIQUE (parent, slug)',
                'The URI (Parent + SLUG) of the Galatea URI must be unique.'),
            ]

    @classmethod
    def validate(cls, uris):
        super(GalateaUri, cls).validate(uris)
        cls.check_recursion(uris)

    @classmethod
    def default_website(cls):
        Website = Pool().get('galatea.website')
        websites = Website.search([('active', '=', True)])
        if len(websites) == 1:
            return websites[0].id

    @fields.depends('name', 'slug')
    def on_change_name(self):
        if self.name and not self.slug:
            return {
                'slug': slugify(self.name),
                }
        return {}

    @fields.depends('slug')
    def on_change_slug(self):
        if self.slug:
            return {
                'slug': slugify(self.slug),
                }

    @staticmethod
    def default_left():
        return 0

    @staticmethod
    def default_right():
        return 0

    @staticmethod
    def default_sequence():
        return 1

    def get_uri(self, name):
        def _get_uri_recursive(uri):
            if uri.parent:
                return '%s/%s' % (_get_uri_recursive(uri.parent), uri.slug)
            return '/%s' % uri.slug

        uri = _get_uri_recursive(self)

        locale = Transaction().context.get('language', 'en')
        if (not uri.startswith('/%s/' % locale[:2])
                and uri != '/%s' % locale[:2]):
            uri = '/%s%s' % (locale[:2], uri)

        if self.website.uri and self.website.uri != '/':
            uri = '%s%s' % (self.website.uri, uri)
        return uri

    @classmethod
    def search_uri(cls, name, clause):
        # TODO
        return [
            ('slug',) + tuple(clause[1:]),
            ]

    @staticmethod
    def default_type():
        return 'content'

    @classmethod
    def get_content_types(cls, uri=None):
        res = [(None, '')]
        if uri and uri.template:
            res += [(m.model, m.name) for m in uri.template.allowed_models]
        return res

    @fields.depends('content')
    def on_change_with_content_model(self, name=None):
        pool = Pool()
        Model = pool.get('ir.model')
        if self.content:
            return Model.search([
                    ('model', '=', self.content.__class__.__name__),
                    ])[0].id

    @staticmethod
    def default_active():
        return True

    @property
    def breadcrumb(self):
        if self.parent:
            res = self.parent.breadcrumb()
        else:
            res = []
        res.append(self)
        return res
