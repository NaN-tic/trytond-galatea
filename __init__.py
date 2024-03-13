# This file is part galatea module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.pool import Pool
from . import attachment
from . import galatea
from . import resource
from . import static_file
from . import party


def register():
    Pool.register(
        attachment.Attachment,
        galatea.GalateaWebSite,
        galatea.GalateaWebsiteCountry,
        galatea.GalateaWebsiteLang,
        galatea.GalateaWebsiteCurrency,
        galatea.GalateaUser,
        galatea.GalateaUserWebSite,
        galatea.GalateaRemoveCacheStart,
        galatea.GalateaSendPasswordStart,
        galatea.GalateaSendPasswordResult,
        resource.GalateaTemplateParameter,
        resource.GalateaTemplate,
        resource.GalateaTemplateModel,
        resource.GalateaTemplateParameterModel,
        resource.GalateaUri,
        resource.GalateaUriValue,
        static_file.GalateaStaticFolder,
        static_file.GalateaStaticFile,
        party.Party,
        party.Address,
        module='galatea', type_='model')
    Pool.register(
        galatea.GalateaRemoveCache,
        galatea.GalateaSendPassword,
        party.PartyReplace,
        module='galatea', type_='wizard')
