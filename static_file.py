# This file is part galatea module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
import os
import os.path
import urllib.request, urllib.parse, urllib.error

from trytond.model import ModelSQL, ModelView, fields, Unique
from trytond.pool import Pool
from trytond.pyson import Eval, Not, Equal
from trytond.transaction import Transaction
from trytond.config import config
from trytond.i18n import gettext
from trytond.exceptions import UserError
from .tools import slugify, slugify_file


__all__ = ['GalateaStaticFolder', 'GalateaStaticFile']


class GalateaStaticFolder(ModelSQL, ModelView):
    "Static folder for Galatea"
    __name__ = "galatea.static.folder"
    name = fields.Char('Name', required=True,
        help='Folder name contains az09 characters')
    description = fields.Char('Description', select=1)
    files = fields.One2Many('galatea.static.file', 'folder', 'Files')

    @classmethod
    def __setup__(cls):
        super(GalateaStaticFolder, cls).__setup__()
        table = cls.__table__()
        cls._sql_constraints += [
            ('unique_folder', Unique(table, table.name),
             'Folder name needs to be unique')
        ]

    @fields.depends('name')
    def on_change_with_name(self):
        """
        Slugified folder name
        """
        if self.name:
            return slugify(self.name)

    @classmethod
    def validate(cls, files):
        for file_ in files:
            file_.check_name()
        super(GalateaStaticFolder, cls).validate(files)

    def check_name(self):
        '''
        Check the validity of folder name
        Allowing the use of / or . will be risky as that could
        eventually lead to previlege escalation
        '''
        if ('.' in self.name) or (self.name.startswith('/')):
            raise UserError(gettext('galatea.invalid_name'))

    @classmethod
    def write(cls, folders, vals):
        """
        Check if the folder name has been modified.
        If yes, raise an error.

        :param vals: values of the current record
        """
        if vals.get('name'):
            # TODO: Support this feature in future versions
            raise UserError(gettext('galatea.folder_cannot_change'))
        return super(GalateaStaticFolder, cls).write(folders, vals)

    @classmethod
    def copy(cls, files, default=None):
        raise UserError(gettext('galatea.not_allow_copy'))


class GalateaStaticFile(ModelSQL, ModelView):
    "Static files for Galatea"
    __name__ = "galatea.static.file"
    name = fields.Char('File Name', required=True)
    folder = fields.Many2One('galatea.static.folder', 'Folder', states={
            'required': Equal(Eval('type'), 'local'),
            })
    type = fields.Selection([
            ('local', 'Local File'),
            ('remote', 'Remote File'),
            ], 'File Type')
    remote_path = fields.Char('Remote File', select=True, translate=True,
        states={
            'required': Equal(Eval('type'), 'remote'),
            'invisible': Not(Equal(Eval('type'), 'remote'))
            })
    file_binary = fields.Function(fields.Binary('File', filename='name'),
        'get_file_binary', 'set_file_binary')
    file_path = fields.Function(fields.Char('File Path'),
        'get_file_path')
    url = fields.Function(fields.Char('URL'),
        'get_url')

    @staticmethod
    def default_folder():
        Folder = Pool().get('galatea.static.folder')
        folders = Folder.search([])
        if len(folders) == 1:
            return folders[0].id

    @staticmethod
    def default_type():
        return 'local'

    def _set_file_binary(self, value):
        """
        Setter for static file that stores file in file system

        :param value: The value to set
        """
        if self.type == 'local' and value:
            file_binary = bytes(value)
            # If the folder does not exist, create it recursively
            directory = os.path.dirname(self.file_path)
            if not os.path.isdir(directory):
                os.makedirs(directory, 0o775)
            os.umask(0o022)
            with open(self.file_path, 'wb') as file_writer:
                file_writer.write(file_binary)

    @classmethod
    def set_file_binary(cls, files, name, value):
        """
        Setter for the functional binary field.

        :param files: Records
        :param name: Ignored
        :param value: The file bytes
        """
        for static_file in files:
            static_file._set_file_binary(value)

    def get_file_binary(self, name):
        '''
        Getter for the binary_file field. This fetches the file from the
        file system, coverts it to bytes and returns it.

        :param name: Field name
        :return: File bytes
        '''
        if self.type == 'local':
            location = self.file_path
            if not os.path.exists(location):
                return
        else:
            try:
                location = urllib.request.urlretrieve(self.remote_path)[0]
            except:
                return

        with open(location, 'rb') as file_reader:
            return fields.Binary.cast(file_reader.read())

    def get_file_path(self, name):
        """
        Returns the full path to the file in the file system

        :param name: Field name
        :return: File path
        """
        return (os.path.abspath(
                os.path.join(
                    self.get_galatea_base_path(),
                    self.folder.name, self.name))
            if self.type == 'local' else self.remote_path)

    @staticmethod
    def get_galatea_base_path():
        """
        Returns base path for galatea, where all the static files would be
        stored.

        By Default it is:

        <Tryton Data Path>/<Database Name>/galatea
        """
        return os.path.join(config.get('database', 'path'),
            Transaction().database.name, "galatea")

    def get_url(self, name):
        """Return the url if within an active request context or return
        False values
        """
        if self.type == 'local':
            return '/galatea-static/%s/%s' % (self.folder.name, self.name)
        elif self.type == 'remote':
            return self.remote_path

    @classmethod
    def validate(cls, static_files):
        super(GalateaStaticFile, cls).validate(static_files)
        for static_file in static_files:
            static_file.check_file_name()

    def check_file_name(self):
        '''
        Check the validity of folder name
        Allowing the use of / or . will be risky as that could
        eventually lead to previlege escalation
        '''
        if ('..' in self.name) or ('/' in self.name):
            raise UserError(gettext('galatea.invalid_file_name'))

    @classmethod
    def create(cls, vlist):
        for vals in vlist:
            vals['name'] = slugify_file(vals['name'])
        return super(GalateaStaticFile, cls).create(vlist)

    @classmethod
    def write(cls, files, values):
        # TODO: Why? maybe a warning
        # if values.get('name'):
        #     raise UserError(gettext('galatea.change_file_name'))
        return super(GalateaStaticFile, cls).write(files, values)

    @classmethod
    def copy(cls, files, default=None):
        raise UserError(gettext('galatea.not_allow_copy'))

    @classmethod
    def delete(cls, files):
        for f in files:
            if f.type == 'local' and os.path.exists(f.file_path):
                os.remove(f.file_path)
        super(GalateaStaticFile, cls).delete(files)
