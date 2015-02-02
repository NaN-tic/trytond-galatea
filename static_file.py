# This file is part galatea module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.model import ModelSQL, ModelView, fields
from trytond.pool import Pool
from trytond.pyson import Eval, Not, Equal
from trytond.transaction import Transaction
from trytond.config import config
from .tools import slugify, slugify_file

import os
import urllib

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
        cls._constraints += [
            ('check_name', 'invalid_name'),
        ]
        cls._sql_constraints += [
            ('unique_folder', 'UNIQUE(name)',
             'Folder name needs to be unique')
        ]
        cls._error_messages.update({
            'invalid_name': """Invalid folder name:
                (1) '.' in folder name (OR)
                (2) folder name begins with '/'""",
            'folder_cannot_change': "Folder name cannot be changed"
        })

    @fields.depends('name')
    def on_change_with_name(self):
        """
        Slugified folder name
        """
        if self.name:
            self.name = slugify(self.name)
            return self.name

    def check_name(self):
        '''
        Check the validity of folder name
        Allowing the use of / or . will be risky as that could
        eventually lead to previlege escalation
        '''
        if ('.' in self.name) or (self.name.startswith('/')):
            return False
        return True

    @classmethod
    def write(cls, folders, vals):
        """
        Check if the folder name has been modified.
        If yes, raise an error.

        :param vals: values of the current record
        """
        if vals.get('name'):
            # TODO: Support this feature in future versions
            cls.raise_user_error('folder_cannot_change')
        return super(GalateaStaticFolder, cls).write(folders, vals)


class GalateaStaticFile(ModelSQL, ModelView):
    "Static files for Galatea"
    __name__ = "galatea.static.file"
    name = fields.Char('File Name', required=True)
    folder = fields.Many2One('galatea.static.folder', 'Folder',
        states={
            'required': Equal(Eval('type'), 'local'),
        })
    type = fields.Selection([
        ('local', 'Local File'),
        ('remote', 'Remote File'),
        ], 'File Type')
    remote_path = fields.Char(
        'Remote File', select=True, translate=True,
        states={
            'required': Equal(Eval('type'), 'remote'),
            'invisible': Not(Equal(Eval('type'), 'remote'))
        })
    file_binary = fields.Function(fields.Binary('File', filename='name'),
        'get_file_binary', 'set_file_binary')
    file_path = fields.Function(fields.Char('File Path'), 'get_file_path')
    url = fields.Function(fields.Char('URL'), 'get_url')

    @classmethod
    def __setup__(cls):
        super(GalateaStaticFile, cls).__setup__()
        cls._constraints += [
            ('check_file_name', 'invalid_file_name'),
            ]
        cls._error_messages.update({
            'invalid_file_name': """Invalid file name:
                (1) '..' in file name (OR)
                (2) file name contains '/'""",
            'change_file_name': "You can't change file name",
            })

    @staticmethod
    def default_type():
        return 'local'

    @staticmethod
    def default_folder():
        Folder = Pool().get('galatea.static.folder')
        folders = Folder.search([])
        if len(folders) == 1:
            return folders[0].id

    @classmethod
    def create(cls, vlist):
        for vals in vlist:
            vals['name'] = slugify_file(vals['name'])
        return super(GalateaStaticFile, cls).create(vlist)

    @classmethod
    def write(cls, files, values):
        if values.get('name'):
            cls.raise_user_error('change_file_name')
        return super(GalateaStaticFile, cls).write(files, values)

    @classmethod
    def delete(cls, files):
        for f in files:
            if f.type == 'local':
                os.remove(f.file_path)
        super(GalateaStaticFile, cls).delete(files)

    def check_file_name(self):
        '''
        Check the validity of folder name
        Allowing the use of / or . will be risky as that could
        eventually lead to previlege escalation
        '''
        if ('..' in self.name) or ('/' in self.name):
            return False
        return True

    def _set_file_binary(self, value):
        """
        Setter for static file that stores file in file system

        :param value: The value to set
        """
        if self.type == 'local':
            file_binary = buffer(value)
            # If the folder does not exist, create it recursively
            directory = os.path.dirname(self.file_path)
            if not os.path.isdir(directory):
                os.makedirs(directory)
            with open(self.file_path, 'wb') as file_writer:
                file_writer.write(file_binary)

    @classmethod
    def set_file_binary(cls, files, name, value):
        """
        Setter for the functional binary field.

        :param files: Records
        :param name: Ignored
        :param value: The file buffer
        """
        for static_file in files:
            static_file._set_file_binary(value)

    def get_file_binary(self, name):
        '''
        Getter for the binary_file field. This fetches the file from the
        file system, coverts it to buffer and returns it.

        :param name: Field name
        :return: File buffer
        '''
        location = self.file_path if self.type == 'local' \
            else urllib.urlretrieve(self.remote_path)[0]
        with open(location, 'rb') as file_reader:
            return buffer(file_reader.read())

    def get_file_path(self, name):
        """
        Returns the full path to the file in the file system

        :param name: Field name
        :return: File path
        """
        return os.path.abspath(
            os.path.join(
                self.get_galatea_base_path(),
                self.folder.name, self.name
            )) \
            if self.type == 'local' else self.remote_path

    def get_url(self, name):
        """Return the url if within an active request context or return
        False values
        """
        if self.type == 'local':
            return '/galatea-static/%s/%s' % (self.folder.name, self.name)
        elif self.type == 'remote':
            return self.remote_path

    @staticmethod
    def get_galatea_base_path():
        """
        Returns base path for galatea, where all the static files would be
        stored.

        By Default it is:

        <Tryton Data Path>/<Database Name>/galatea
        """
        cursor = Transaction().cursor
        return os.path.join(
            config.get('database', 'path'), cursor.database_name, "galatea"
        )
