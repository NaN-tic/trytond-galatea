# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.model import ModelSQL, ModelView, fields
from trytond.pool import Pool
from trytond.pyson import Bool, If, Eval, Greater
from trytond.transaction import Transaction

from .tools import slugify

__all__ = ['GalateaTemplate', 'GalateaTemplateModel',
    'GalateaUri', 'GalateaVisiblePage']


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
    _order = [('parent', 'ASC'), ('sequence', 'ASC'), ('id', 'ASC')]

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
    redirection_code = fields.Selection([
            ('301', '301:'),
            ('302', '302:'),
            ('303', '303:'),
            ('305', '305:'),
            ('307', '307:'),
            ], 'Redirection Code', sort=False,
        states={
            'invisible': ~Eval('type').in_(['internal_redirection',
                    'external_redirection']),
            'required': Eval('type').in_(['internal_redirection',
                    'external_redirection']),
            })
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
        if (len(clause) == 3 and isinstance(clause[2], basestring)
                and len(clause[2].split('/')) > 1):
            slugs = clause[2].split('/')
            # TODO
            domain = [
                ('slug', clause[1], slugs.pop()),
                ]
            prefix = 'parent.'
            while slugs:
                domain.append((prefix + 'slug', clause[1], slugs.pop()))
                prefix += 'parent.'
            return domain
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
    def default_redirection_code():
        return '303'

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


class GalateaVisiblePage(ModelSQL, ModelView):
    '''Galatea Visible Page'''

    # TODO: it should be "title"
    name = fields.Char('Title', translate=True,
        required=True, on_change=['name', 'slug'])
    canonical_uri = fields.Many2One('galatea.uri', 'Canonical URI',
        required=True, select=True, domain=[
            # TODO: fail with tag websites functional field
            # ('website', 'in', Eval('websites')),
            ('type', '=', 'content'),
            # This domain clause must to be added in setup() of each subclass
            # ('template.allowed_models.model', 'in', ['galatea.blog.post']),
            ],
        states={
            'required': Greater(Eval('id', -1), 0),
            'invisible': ~Greater(Eval('id', -1), 0),
            }, depends=['websites', 'id'])
    slug = fields.Function(fields.Char('Slug', translate=True, required=True),
        'on_change_with_slug', setter='set_canonical_uri_field',
        searcher='search_canonical_uri_field')
    template = fields.Function(fields.Many2One('galatea.template', 'Template',
            required=True),
        'on_change_with_template', setter='set_canonical_uri_field',
        searcher='search_canonical_uri_field')
    uris = fields.One2Many('galatea.uri', 'content', 'URIs', readonly=True)
    uri = fields.Function(fields.Many2One('galatea.uri', 'URI'),
        'get_uri', searcher='search_uri')
    # TODO: replace by uri_langs?
    # slug_langs = fields.Function(fields.Dict(None, 'Slug Langs'),
    #     'get_slug_langs')
    # _slug_langs_cache = Cache('galatea_blog_post.slug_langs')
    # TODO: maybe websites should be a searchable functional field as sum of
    # canonical_uri/uris website field
    # websites = fields.Many2Many('galatea.cms.article-galatea.website',
    #     'article', 'website', 'Websites', required=True,
    #     help='Tutorial will be available in those websites')
    visibility = fields.Selection([
            ('public', 'Public'),
            ('register', 'Register'),
            ('manager', 'Manager'),
            ], 'Visibility', required=True)
    # TODO: extend getter/setter/searcher to all uris (is active is some uri is
    # active)
    active = fields.Function(fields.Boolean('Active',
            help='Dissable to not show this content.'),
        'get_active', setter='set_canonical_uri_field',
        searcher='search_canonical_uri_field')
    # TODO: move here also the "SEO" fields? (metatitle/description/keywords)

    @classmethod
    def __setup__(cls):
        super(GalateaVisiblePage, cls).__setup__()

        uri_domain_clause = ('template.allowed_models.model', 'in',
            [cls.__name__]),
        for clause in cls.canonical_uri.domain:
            if isinstance(clause, tuple) and clause == uri_domain_clause:
                break
        else:
            cls.canonical_uri.domain.append(uri_domain_clause)

    @fields.depends('name', 'slug')
    def on_change_name(self):
        res = {}
        if self.name and not self.slug:
            res['slug'] = slugify(self.name)
        return res

    @fields.depends('canonical_uri', 'slug')
    def on_change_with_slug(self, name=None):
        if self.slug:
            return slugify(self.slug)
        if self.canonical_uri:
            return self.canonical_uri.slug

    @fields.depends('canonical_uri')
    def on_change_with_template(self, name=None):
        if self.canonical_uri:
            return self.canonical_uri.template.id

    @classmethod
    def set_canonical_uri_field(cls, records, name, value):
        pool = Pool()
        Uri = pool.get('galatea.uri')
        Uri.write([r.canonical_uri for r in records if r.canonical_uri], {
                name: value,
                })

    @classmethod
    def search_canonical_uri_field(cls, name, clause):
        domain = [
            ('canonical_uri.%s' % name,) + tuple(clause[1:]),
            ]
        if clause == ['active', '=', False]:
            domain = [
                'OR',
                domain,
                [('canonical_uri', '=', None)],
                ]
        return domain

    # TODO: replace by uri_langs?
    # def get_slug_langs(self, name):
    #     'Return dict slugs for each active languages'
    #     pool = Pool()
    #     Lang = pool.get('ir.lang')
    #     Post = pool.get('galatea.blog.post')

    #     post_id = self.id
    #     langs = Lang.search([
    #         ('active', '=', True),
    #         ('translatable', '=', True),
    #         ])

    #     slugs = {}
    #     for lang in langs:
    #         with Transaction().set_context(language=lang.code):
    #             post, = Post.read([post_id], ['slug'])
    #             slugs[lang.code] = post['slug']

    #     return slugs

    def get_uri(self, name):
        context = Transaction().context
        if context.get('website', False):
            for uri in self.uris:
                if uri.website.id == context['website']:
                    return uri.id
        return self.canonical_uri.id

    @classmethod
    def search_uri(cls, name, clause):
        context = Transaction().context
        if context.get('website', False):
            # TODO: is it better and If()?
            return [
                ['OR', [
                    ('canonical_uri',) + tuple(clause[1:]),
                    ('website', '=', context['website']),
                    ], [
                    ('uris',) + tuple(clause[1:]),
                    ('website', '=', context['website']),
                    ]],
                ]
        return [
            ['OR', [
                ('canonical_uri',) + tuple(clause[1:]),
                ], [
                ('uris',) + tuple(clause[1:]),
                ]],
            ]

    # @classmethod
    # def default_websites(cls):
    #     Website = Pool().get('galatea.website')
    #     websites = Website.search([('active', '=', True)])
    #     return [w.id for w in websites]

    @staticmethod
    def default_visibility():
        return 'public'

    @staticmethod
    def default_active():
        return True

    def get_active(self, name):
        if self.canonical_uri and self.canonical_uri.active:
            return True
        return any(u.active for u in self.uris)

    @classmethod
    def create(cls, vlist):
        pool = Pool()
        Uri = pool.get('galatea.uri')

        vlist = [x.copy() for x in vlist]
        for vals in vlist:
            if not vals.get('canonical_uri'):
                assert vals.get('slug')
                assert vals.get('websites')
                uri_vals = cls.calc_uri_vals(vals)
                uri, = Uri.create([uri_vals])
                vals['canonical_uri'] = uri.id
        new_records = super(GalateaVisiblePage, cls).create(vlist)

        uri_args = []
        for record in new_records:
            if not record.canonical_uri.content:
                uri_args.extend(([record.canonical_uri], {
                        'content': str(record),
                        }))
        if uri_args:
            Uri.write(*uri_args)
        return new_records

    @classmethod
    def calc_uri_vals(cls, record_vals):
        website_id = [websites
            for action, websites in record_vals['websites']
            if action == 'add'][0][0]

        return {
            'website': website_id,
            # 'parent': ,
            'name': record_vals['name'],
            'slug': record_vals['slug'],
            'type': 'content',
            # 'template': ,
            'active': record_vals.get('active', cls.default_active()),
            }

    @classmethod
    def copy(cls, records, default=None):
        pool = Pool()
        Uri = pool.get('galatea.uri')

        if default is None:
            default = {}
        else:
            default = default.copy()

        new_records = []
        for record in records:
            default['canonical_uri'], = Uri.copy([record.canonical_uri], {
                    'slug': '%s-copy' % record.slug,
                    })
            new_records += super(GalateaVisiblePage, cls).copy([record],
                default=default)
        return new_records

    @classmethod
    def write(cls, *args):
        pool = Pool()
        Uri = pool.get('galatea.uri')

        actions = iter(args)
        uri_args = []
        for records, values in zip(actions, actions):
            if values.get('canonical_uri'):
                canonical_uri = Uri(values['canonical_uri'])
                canonical_uri.content = records[0]
                canonical_uri.save()
            if 'name' in values:
                uri_todo = []
                for record in records:
                    if record.canonical_uri.name == record.name:
                        uri_todo.append(record.canonical_uri)
                    for uri in record.uris:
                        if uri.name == record.name and uri not in uri_todo:
                            uri_todo.append(uri)
                if uri_todo:
                    # What happens if canonical_uri and name change?
                    uri_args.append(uri_todo)
                    uri_args.append({
                            'name': values['name'],
                            })

        super(GalateaVisiblePage, cls).write(*args)
        if uri_args:
            Uri.write(*uri_args)

    @classmethod
    def delete(cls, pages):
        pool = Pool()
        Uri = pool.get('galatea.uri')

        uris_to_delete = set()
        for page in pages:
            uris_to_delete.add(page.canonical_uri)
            for uri in page.uris:
                uris_to_delete.add(uri)
        super(GalateaVisiblePage, cls).delete(pages)
        Uri.delete(list(uris_to_delete))
