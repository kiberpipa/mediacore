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

from pylons.i18n import _
from pylons import config, request

from mediacore.lib.base import BaseController
from mediacore.lib.decorators import expose, observable
from mediacore.lib.helpers import redirect, clean_xhtml
from mediacore.lib import email as libemail
from mediacore.plugin import events

class ErrorController(BaseController):
    """Generates error documents as and when they are required.

    The ErrorDocuments middleware forwards to ErrorController when error
    related status codes are returned from the application.

    This behaviour can be altered by changing the parameters to the
    ErrorDocuments middleware in your config/middleware.py file.
    """
    @expose('error.html')
    @observable(events.ErrorController.document)
    def document(self, *args, **kwargs):
        """Render the error document for the general public.

        Essentially, when an error occurs, a second request is initiated for
        the URL ``/error/document``. The URL is set on initialization of the
        :class:`pylons.middleware.StatusCodeRedirect` object, and can be
        overridden in :func:`tg.configuration.add_error_middleware`. Also,
        before this method is called, some potentially useful environ vars
        are set in :meth:`pylons.middleware.StatusCodeRedirect.__call__`
        (access them via :attr:`tg.request.environ`).

        :rtype: Dict
        :returns:
            prefix
                The environ SCRIPT_NAME.
            vars
                A dict containing the first 2 KB of the original request.
            code
                Integer error code thrown by the original request, but it can
                also be overriden by setting ``tg.request.params['code']``.
            message
                A message to display to the user. Pulled from
                ``tg.request.params['message']``.

        """
        request = self._py_object.request
        environ = request.environ
        original_request = environ.get('pylons.original_request', None)
        original_response = environ.get('pylons.original_response', None)
        default_message = '<p>%s</p>' % _("We're sorry but we weren't able "
                                          "to process this request.")

        message = request.params.get('message', default_message)
        message = clean_xhtml(message)

        return dict(
            prefix = environ.get('SCRIPT_NAME', ''),
            code = int(request.params.get('code', getattr(original_response,
                                                          'status_int', 500))),
            message = message,
            vars = dict(POST_request=unicode(original_request)[:2048]),
        )

    @expose()
    @observable(events.ErrorController.report)
    def report(self, email='', description='', **kwargs):
        """Email a support request that's been submitted on :meth:`document`.

        Redirects back to the root URL ``/``.

        """
        url = ''
        get_vars = post_vars = {}
        for x in kwargs:
            if x.startswith('GET_'):
                get_vars[x] = kwargs[x]
            elif x.startswith('POST_'):
                post_vars[x] = kwargs[x]
        libemail.send_support_request(email, url, description, get_vars, post_vars)
        redirect('/')
