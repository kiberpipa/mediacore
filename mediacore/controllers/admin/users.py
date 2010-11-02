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

from pylons import request, response, session, tmpl_context
from repoze.what.predicates import has_permission
from sqlalchemy import orm, sql
import webob.exc

from mediacore.forms.admin.users import UserForm
from mediacore.lib import helpers
from mediacore.lib.base import BaseController
from mediacore.lib.decorators import expose, expose_xhr, observable, paginate, validate
from mediacore.lib.helpers import redirect, url_for
from mediacore.model import Group, User, fetch_row, get_available_slug
from mediacore.model.meta import DBSession
from mediacore.plugin import events

user_form = UserForm()

class UsersController(BaseController):
    """Admin user actions"""
    allow_only = has_permission('admin')

    @expose_xhr('admin/users/index.html')
    @paginate('users', items_per_page=50)
    @observable(events.Admin.UsersController.index)
    def index(self, page=1, **kwargs):
        """List users with pagination.

        :param page: Page number, defaults to 1.
        :type page: int
        :rtype: Dict
        :returns:
            users
                The list of :class:`~mediacore.model.auth.User`
                instances for this page.

        """
        users = DBSession.query(User).order_by(User.display_name,
                                               User.email_address)
        return dict(users=users)


    @expose('admin/users/edit.html')
    @observable(events.Admin.UsersController.edit)
    def edit(self, id, **kwargs):
        """Display the :class:`~mediacore.forms.admin.users.UserForm` for editing or adding.

        :param id: User ID
        :type id: ``int`` or ``"new"``
        :rtype: dict
        :returns:
            user
                The :class:`~mediacore.model.auth.User` instance we're editing.
            user_form
                The :class:`~mediacore.forms.admin.users.UserForm` instance.
            user_action
                ``str`` form submit url
            user_values
                ``dict`` form values

        """
        user = fetch_row(User, id)

        if tmpl_context.action == 'save' or id == 'new':
            # Use the values from error_handler or GET for new users
            user_values = kwargs
            user_values['login_details.password'] = None
            user_values['login_details.confirm_password'] = None
        else:
            user_values = dict(
                display_name = user.display_name,
                email_address = user.email_address,
                login_details = dict(
                    group = user.groups and user.groups[0].group_id or None,
                    user_name = user.user_name,
                ),
            )

        return dict(
            user = user,
            user_form = user_form,
            user_action = url_for(action='save'),
            user_values = user_values,
        )


    @expose()
    @validate(user_form, error_handler=edit)
    @observable(events.Admin.UsersController.save)
    def save(self, id, email_address, display_name, login_details,
             delete=None, **kwargs):
        """Save changes or create a new :class:`~mediacore.model.auth.User` instance.

        :param id: User ID. If ``"new"`` a new user is created.
        :type id: ``int`` or ``"new"``
        :returns: Redirect back to :meth:`index` after successful save.

        """
        user = fetch_row(User, id)

        if delete:
            DBSession.delete(user)
            redirect(action='index', id=None)

        user.display_name = display_name
        user.email_address = email_address
        user.user_name = login_details['user_name']

        password = login_details['password']
        if password is not None and password != '':
            user.password = password

        if login_details['group']:
            group = fetch_row(Group, login_details['group'])
            user.groups = [group]
        else:
            user.groups = []

        DBSession.add(user)

        # Check if we're changing the logged in user's own password
        logged_in_user = request.environ['repoze.who.identity']['user']
        if user.user_id == logged_in_user.user_id \
        and password is not None and password != '':
            DBSession.commit()
            # repoze.who sees the Unauthorized response and clears the cookie,
            # forcing a fresh login with the new password
            raise webob.exc.HTTPUnauthorized

        redirect(action='index', id=None)


    @expose('json')
    @observable(events.Admin.UsersController.delete)
    def delete(self, id, **kwargs):
        """Delete a user.

        :param id: User ID.
        :type id: ``int``
        :returns: Redirect back to :meth:`index` after successful delete.
        """
        user = fetch_row(User, id)
        DBSession.delete(user)

        if request.is_xhr:
            return dict(success=True)
        redirect(action='index', id=None)
