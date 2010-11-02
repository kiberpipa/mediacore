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

import logging
import os
import re

from genshi.template import loader
from importlib import import_module
from paste.urlmap import URLMap
from paste.urlparser import StaticURLParser
from pkg_resources import iter_entry_points, resource_exists, resource_filename
from pylons.util import class_name_from_module_name
from pylons.wsgiapp import PylonsApp
from routes.util import controller_scan

log = logging.getLogger(__name__)

class PluginManager(object):
    """
    Plugin Loading and Management

    This class is responsible for loading plugins that define an entry point
    within the group 'mediacore.plugin'. It introspects the plugin module to
    find any templates, public static files, or controllers it may provide.
    Names and paths are based on the name of the entry point, and should be
    unique.

    Plugins may also register event observers and/or implement interfaces
    as a result of being loaded, but we do not handle any of that here.

    """
    def __init__(self, config):
        log.debug('Initializing plugins')
        self.config = config
        self.DEBUG = config['debug']
        self.plugins = {}
        self._match_templates = {}

        for epoint in iter_entry_points('mediacore.plugin'):
            # TODO: Check the config to see if this plugin should be enabled.
            module = epoint.load()
            plugin_class = getattr(module, '__plugin__', _Plugin)
            self.plugins[epoint.name] = plugin_class(module, epoint.name)
            log.debug('Plugin loaded: %r', epoint)

    def public_paths(self):
        """Return a dict of all 'public' folders in the loaded plugins.

        :returns: A dict keyed by the plugin public directory for use in
            URLs, the value being the absolute path to the directory that
            contains the static files.
        """
        paths = {}
        for name, plugin in self.plugins.iteritems():
            if plugin.public_path:
                paths['/' + name + '/public'] = plugin.public_path
        log.debug('Public paths: %r', paths)
        return paths

    def template_loaders(self):
        """Return genshi loaders for all the plugins that provide templates.

        Plugin template are found under its module name::

            <xi:include "{plugin.name}/index.html" />

        Maps to::

            `{path_to_module}/templates/index.html`

        :rtype: list
        :returns: Instances of :class:`genshi.template.loader.TemplateLoader`
        """
        loaders = {}
        for name, plugin in self.plugins.iteritems():
            if plugin.templates_path:
                loaders[name] = plugin.templates_path
        if loaders:
            log.debug('Template loaders: %r', loaders)
            return [loader.prefixed(**loaders)]
        return []

    def match_templates(self, template):
        """Return plugin templates that should be included into to the given template.

        This is easiest explained by example: to extend the `media/view.html` template,
        your plugin should provide its own `media/view.html` file in its templates
        directory. This override template would be directly includable like so::

            /{plugin.name}/media/view.html

        Typically this file would use Genshi's `py:match directive
        <http://genshi.edgewall.org/wiki/Documentation/xml-templates.html#id5>`_
        to hook and wrap or replace certain tags within the core output.

        :param template: A relative template include path, which the Genshi
            loader will later resolve.
        :rtype: list
        :returns: Relative paths ready for use in <xi:include> in a Genshi template.
        """
        template = os.path.normpath(template)
        if template in self._match_templates and not self.DEBUG:
            matches = self._match_templates[template]
        else:
            matches = self._match_templates[template] = []
            for name, plugin in self.plugins.iteritems():
                templates_path = plugin.templates_path
                if templates_path is not None \
                and os.path.exists(os.path.join(templates_path, template)):
                    matches.append(os.path.sep + os.path.join(name, template))
        return matches

    def controller_classes(self):
        """Return a dict of controller classes that plugins have defined.

        Plugin modules are introspected for an attribute named either:

            * `__controller__` or
            * `{Modulename}Controller`

        In both cases, the controller "name" as far as the application
        (including routes) is concerned is the module name.

        :rtype: dict
        :returns: A mapping of controller names to controller classes.
        """
        classes = {}
        for plugin in self.plugins.itervalues():
            classes.update(plugin.controllers)
        return classes

    def controller_scan(self, directory):
        """Extend the controller discovery by routes with our plugin controllers.

        :param directory: The full path to the core controllers directory.
        :rtype: list
        :returns: Controller names
        """
        return controller_scan(directory) + self.controller_classes().keys()

    def wrap_pylons_app(self, app):
        """Pass PylonsApp our controllers to bypass its autodiscovery.

        :meth:`pylons.wsgiapp.PylonsApp.find_controller` is pretty limited
        in where it will try to import controllers from. However, it does
        cache the controllers it has imported in a public dictionary. We
        pass the plugin controllers that we've discovered to bypass the
        standard Pylons discovery method.

        XXX: This relies on an undocumented feature of PylonsApp. We'll
             need to subclass instead if this API changes.

        :param app: The :class:`pylons.wsgiapp.PylonsApp` instance.
        :returns: The :class:`pylons.wsgiapp.PylonsApp` instance.
        """
        if isinstance(app, PylonsApp):
            app.controller_classes = self.controller_classes()
            log.debug('App wrapped')
        else:
            log.warn('The given app %r is NOT an instance of PylonsApp', app)
        return app

class _Plugin(object):
    """
    Plugin Metadata

    This houses all the conventions for where resources should be found
    within a plugin module. A plugin author could potentially extend this
    class to redefine these conventions according to their needs. Besides
    that, it gives us a convenient place to store this data for repeated
    use.

    """
    def __init__(self, module, name, templates_path=None,
                 public_path=None, controllers=None):
        self.module = module
        self.modname = module.__name__
        self.name = name
        self.templates_path = templates_path or self._default_templates_path()
        self.public_path = public_path or self._default_public_path()
        self.controllers = controllers or self._default_controllers()

    def _default_templates_path(self):
        if resource_exists(self.modname, 'templates'):
            return resource_filename(self.modname, 'templates')
        return None

    def _default_public_path(self):
        if resource_exists(self.modname, 'public'):
            return resource_filename(self.modname, 'public')
        return None

    def _default_controllers(self):
        # Find controllers in the root plugin __init__.py
        controller_class = _controller_class_from_module(self.module, self.name)
        if controller_class:
            return {self.name: controller_class}
        controllers = {}
        # Search a controllers directory, standard pylons style
        if resource_exists(self.modname, 'controllers'):
            directory = resource_filename(self.modname, 'controllers')
            for name in controller_scan(directory):
                module_name = '.'.join([self.modname, 'controllers',
                                        name.replace('/', '.')])
                module = import_module(module_name)
                mycontroller = _controller_class_from_module(module, name)
                if mycontroller is None:
                    log.warn('Controller expected but not found in: %r', module)
                controllers[self.name + '/' + name] = mycontroller
        return controllers

def _controller_class_from_module(module, name):
    c = getattr(module, '__controller__', None)
    if c is None:
        name = name.rsplit('/', 1)[-1]
        class_name = class_name_from_module_name(name) + 'Controller'
        c = getattr(module, class_name, None)
    return c
