# This file is part galatea module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.pool import Pool
from .galatea import *
from .static_file import *
from .party import *

def register():
    Pool.register(
        GalateaWebSite,
        GalateaWebsiteCountry,
        GalateaWebsiteCurrency,
        GalateaUser,
        GalateaUserWebSite,
        GalateaSendPasswordStart,
        GalateaSendPasswordResult,
        GalateaStaticFolder,
        GalateaStaticFile,
        Party,
        module='galatea', type_='model')
    Pool.register(
        GalateaSendPassword,
        module='galatea', type_='wizard')
