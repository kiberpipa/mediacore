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
import os.path

from genshi import Markup, XML
from genshi.output import XHTMLSerializer
from genshi.template.loader import TemplateLoader, directory, TemplateNotFound
from pylons import app_globals
from pylons.templating import pylons_globals

__all__ = ['render', 'render_stream', 'TemplateLoader', 'XHTMLPlusSerializer']

log = logging.getLogger(__name__)

def render(template, tmpl_vars=None, method=None):
    """Generate a markup stream from the given template and vars.

    :param template: A template path.
    :param tmpl_vars: A dict of variables to pass into the template.
    :param method: Optional serialization method for Genshi to use.
        If None, we don't serialize the markup stream into a string.
        Provide 'auto' to use the best guess. See :func:`render_stream`.
    :rtype: :class:`genshi.Stream` or :class:`genshi.Markup`
    :returns: An iterable markup stream, or a serialized markup string
        if `method` was not None.

    """
    if tmpl_vars is None:
        tmpl_vars = {}
    assert isinstance(tmpl_vars, dict), \
        'tmpl_vars must be a dict or None, given: %r' % tmpl_vars

    # Steal a page from TurboGears' book:
    # include the genshi XML helper for convenience in templates.
    tmpl_vars.setdefault('XML', XML)
    tmpl_vars.update(pylons_globals())

    # Pass in all the plugin templates that will manipulate this template
    # The idea is that these paths should be <xi:include> somewhere in the
    # top of the template file.
    plugin_templates = app_globals.plugin_mgr.match_templates(template)
    tmpl_vars['plugin_templates'] = plugin_templates

    # Grab a template reference and apply the template context
    tmpl = app_globals.genshi_loader.load(template)
    stream = tmpl.generate(**tmpl_vars)

    if method is None:
        return stream
    else:
        return render_stream(stream, method=method, template_name=template)

def render_stream(stream, method='auto', template_name=None):
    """Render the given stream to a unicode Markup string.

    We substitute the standard XHTMLSerializer with our own
    :class:`XHTMLPlusSerializer` which is (more) HTML5-aware.

    :type stream: :class:`genshi.Stream`
    :param stream: An iterable markup stream.
    :param method: The serialization method for Genshi to use.
        If given 'auto', the default value, we assume xhtml unless
        a template name is given with an xml extension.
    :param template_name: Optional template name which we use only to
        guess what method to use, if one hasn't been explicitly provided.
    :rtype: :class:`genshi.Markup`
    :returns: A subclassed `unicode` object.

    """
    if method == 'auto':
        if template_name and template_name.endswith('.xml'):
            method = 'xml'
        else:
            method = 'xhtml'

    if method == 'xhtml':
        method = XHTMLPlusSerializer

    return Markup(stream.render(method=method, encoding=None))

class XHTMLPlusSerializer(XHTMLSerializer):
    """Produces XHTML text from an event stream.

    This serializer is aware that <source/> tags are empty, which is
    required for it to be valid (working) HTML5 in some browsers.

    """
    _EMPTY_ELEMS = frozenset(set(['source']) | XHTMLSerializer._EMPTY_ELEMS)

class TemplateLoader(TemplateLoader):
    def load(self, filename, relative_to=None, cls=None, encoding=None):
        """Load the template with the given name.

        XXX: This code copied and modified from Genshi 0.6

        If the `filename` parameter is relative, this method searches the
        search path trying to locate a template matching the given name. If the
        file name is an absolute path, the search path is ignored.

        If the requested template is not found, a `TemplateNotFound` exception
        is raised. Otherwise, a `Template` object is returned that represents
        the parsed template.

        Template instances are cached to avoid having to parse the same
        template file more than once. Thus, subsequent calls of this method
        with the same template file name will return the same `Template`
        object (unless the ``auto_reload`` option is enabled and the file was
        changed since the last parse.)

        If the `relative_to` parameter is provided, the `filename` is
        interpreted as being relative to that path.

        :param filename: the relative path of the template file to load
        :param relative_to: the filename of the template from which the new
                            template is being loaded, or ``None`` if the
                            template is being loaded directly
        :param cls: the class of the template object to instantiate
        :param encoding: the encoding of the template to load; defaults to the
                         ``default_encoding`` of the loader instance
        :return: the loaded `Template` instance
        :raises TemplateNotFound: if a template with the given name could not
                                  be found
        """
        if cls is None:
            cls = self.default_class
        search_path = self.search_path

        # Make the filename relative to the template file its being loaded
        # from, but only if that file is specified as a relative path, or no
        # search path has been set up
        if relative_to and (not search_path or not os.path.isabs(relative_to)):
            filename = os.path.join(os.path.dirname(relative_to), filename)

        filename = os.path.normpath(filename)
        cachekey = filename

        self._lock.acquire()
        try:
            # First check the cache to avoid reparsing the same file
            try:
                tmpl = self._cache[cachekey]
                if not self.auto_reload:
                    return tmpl
                uptodate = self._uptodate[cachekey]
                if uptodate is not None and uptodate():
                    return tmpl
            except (KeyError, OSError):
                pass

            isabs = False

            retry_vars = {}
            if os.path.isabs(filename):
                # Set up secondary search options for template paths that don't
                # resolve with our relative path trick below.
                retry_vars = dict(
                    filename = os.path.basename(filename),
                    relative_to = os.path.dirname(filename) + '/',
                    cls = cls,
                    encoding = encoding
                )
                # Make absolute paths relative to the base search path.
                log.debug('Modifying the default TemplateLoader behaviour '
                          'for path %r; treating the absolute template path '
                          'as relative to the template search path.', filename)
                relative_to = None
                filename = filename[1:] # strip leading slash

            if relative_to and os.path.isabs(relative_to):
                # Make sure that the directory containing the including
                # template is on the search path
                dirname = os.path.dirname(relative_to)
                if dirname not in search_path:
                    search_path = list(search_path) + [dirname]
                isabs = True

            elif not search_path:
                # Uh oh, don't know where to look for the template
                raise TemplateError('Search path for templates not configured')

            for loadfunc in search_path:
                if isinstance(loadfunc, basestring):
                    loadfunc = directory(loadfunc)
                try:
                    filepath, filename, fileobj, uptodate = loadfunc(filename)
                except IOError:
                    continue
                except TemplateNotFound:
                    continue
                else:
                    try:
                        if isabs:
                            # If the filename of either the included or the
                            # including template is absolute, make sure the
                            # included template gets an absolute path, too,
                            # so that nested includes work properly without a
                            # search path
                            filename = filepath
                        tmpl = self._instantiate(cls, fileobj, filepath,
                                                 filename, encoding=encoding)
                        if self.callback:
                            self.callback(tmpl)
                        self._cache[cachekey] = tmpl
                        self._uptodate[cachekey] = uptodate
                    finally:
                        if hasattr(fileobj, 'close'):
                            fileobj.close()
                    return tmpl

            if retry_vars:
                return self.load(**retry_vars)

            raise TemplateNotFound(filename, search_path)

        finally:
            self._lock.release()
