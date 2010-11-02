# This file is a part of MediaCore, Copyright 2009 Simple Station Inc.
#
# MediaCore is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# MediaCore is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""Pylons environment configuration"""
import os
import re
from gettext import GNUTranslations

from genshi.filters.i18n import Translator
from pylons.configuration import PylonsConfig
from pylons.i18n.translation import ugettext, ungettext
from sqlalchemy import engine_from_config

import mediacore.lib.app_globals as app_globals
import mediacore.lib.helpers

from mediacore.config.routing import make_map
from mediacore.lib.auth import classifier_for_flash_uploads
from mediacore.lib.templating import TemplateLoader
from mediacore.model import Media, Podcast, init_model
from mediacore.model.meta import DBSession
from mediacore.plugin import PluginManager, events

def load_environment(global_conf, app_conf):
    """Configure the Pylons environment via the ``pylons.config`` object"""
    config = PylonsConfig()

    # Pylons paths
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    paths = dict(root=root,
                 controllers=os.path.join(root, 'controllers'),
                 static_files=os.path.join(root, 'public'),
                 templates=[os.path.join(root, 'templates')])

    # Initialize config with the basic options
    config.init_app(global_conf, app_conf, package='mediacore', paths=paths)

    # Initialize the plugin manager to load all active plugins
    plugin_mgr = PluginManager(config)

    mapper = make_map(config, plugin_mgr.controller_scan)
    events.Environment.routes(mapper)
    config['routes.map'] = mapper
    config['pylons.app_globals'] = app_globals.Globals(config)
    config['pylons.app_globals'].plugin_mgr = plugin_mgr
    config['pylons.app_globals'].events = events
    config['pylons.h'] = mediacore.lib.helpers

    # Setup cache object as early as possible
    import pylons
    pylons.cache._push_object(config['pylons.app_globals'].cache)

    class DummyTranslators(GNUTranslations):
        ugettext = staticmethod(ugettext)
        ungettext = staticmethod(ungettext)

    def enable_i18n_for_template(template):
        translations = Translator(DummyTranslators())
        translations.setup(template)
        template.filters.insert(0, translations)

    # Create the Genshi TemplateLoader
    config['pylons.app_globals'].genshi_loader = TemplateLoader(
        search_path=paths['templates'] + plugin_mgr.template_loaders(),
        auto_reload=True,
        max_cache_size=100,
        callback=enable_i18n_for_template,
    )

    # Setup the SQLAlchemy database engine
    engine = engine_from_config(config, 'sqlalchemy.')
    init_model(engine, config.get('db_table_prefix', None))
    events.Environment.init_model()

    # CONFIGURATION OPTIONS HERE (note: all config options will override
    #                                   any Pylons config options)

    # TODO: Move as many of these custom options into an .ini file, or at least
    #       to somewhere more friendly.

    # TODO: Rework templates not to rely on this line:
    #       See docstring in pylons.configuration.PylonsConfig for details.
    config['pylons.strict_tmpl_context'] = False

    config['thumb_sizes'] = { # the dimensions (in pixels) to scale thumbnails
        Media._thumb_dir: {
            's': (128,  72),
            'm': (160,  90),
            'l': (560, 315),
        },
        Podcast._thumb_dir: {
            's': (128, 128),
            'm': (160, 160),
            'l': (600, 600),
        },
    }

    # END CUSTOM CONFIGURATION OPTIONS

    events.Environment.loaded(config)

    return config
