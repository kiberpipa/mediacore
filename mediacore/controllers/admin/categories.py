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

from mediacore.forms.admin.categories import CategoryForm, CategoryRowForm
from mediacore.forms.admin.tags import TagForm, TagRowForm
from mediacore.lib.base import BaseController
from mediacore.lib.decorators import expose, expose_xhr, observable, paginate, validate
from mediacore.lib.helpers import redirect, url_for
from mediacore.model import Category, Tag, fetch_row, get_available_slug
from mediacore.model.meta import DBSession
from mediacore.plugin import events

import logging
log = logging.getLogger(__name__)

category_form = CategoryForm()
category_row_form = CategoryRowForm()
tag_form = TagForm()
tag_row_form = TagRowForm()

class CategoriesController(BaseController):
    allow_only = has_permission('edit')

    @expose('admin/categories/index.html')
    @paginate('tags', items_per_page=25)
    @observable(events.Admin.CategoriesController.index)
    def index(self, **kwargs):
        """List categories.

        :rtype: Dict
        :returns:
            categories
                The list of :class:`~mediacore.model.categories.Category`
                instances for this page.
            category_form
                The :class:`~mediacore.forms.admin.settings.categories.CategoryForm` instance.

        """
        categories = Category.query\
            .order_by(Category.name)\
            .options(orm.undefer('media_count'))\
            .populated_tree()

        tags = DBSession.query(Tag)\
            .options(orm.undefer('media_count'))\
            .order_by(Tag.name)

        return dict(
            categories = categories,
            category_form = category_form,
            category_row_form = category_row_form,
            tags = tags,
            tag_form = tag_form,
            tag_row_form = tag_row_form,
        )

    @expose('admin/categories/edit.html')
    @observable(events.Admin.CategoriesController.edit)
    def edit(self, id, **kwargs):
        """Edit a single category.

        :param id: Category ID
        :rtype: Dict
        :returns:
            categories
                The list of :class:`~mediacore.model.categories.Category`
                instances for this page.
            category_form
                The :class:`~mediacore.forms.admin.settings.categories.CategoryForm` instance.

        """
        category = fetch_row(Category, id)

        return dict(
            category = category,
            category_form = category_form,
            category_row_form = category_row_form,
        )

    @expose('json')
    @validate(category_form)
    @observable(events.Admin.CategoriesController.save)
    def save(self, id, delete=None, **kwargs):
        """Save changes or create a category.

        See :class:`~mediacore.forms.admin.settings.categories.CategoryForm` for POST vars.

        :param id: Category ID
        :param delete: If true the category is to be deleted rather than saved.
        :type delete: bool
        :rtype: JSON dict
        :returns:
            success
                bool

        """
        if tmpl_context.form_errors:
            if request.is_xhr:
                return dict(success=False, errors=tmpl_context.form_errors)
            else:
                # TODO: Add error reporting for users with JS disabled?
                return redirect(action='edit')

        cat = fetch_row(Category, id)

        if delete:
            DBSession.delete(cat)
            data = dict(
                success = True,
                id = cat.id,
                parent_options = unicode(category_form.c['parent_id'].display()),
            )
        else:
            cat.name = kwargs['name']
            cat.slug = get_available_slug(Category, kwargs['slug'], cat)

            if kwargs['parent_id']:
                parent = fetch_row(Category, kwargs['parent_id'])
                if parent is not cat and cat not in parent.ancestors():
                    cat.parent = parent
            else:
                cat.parent = None

            DBSession.add(cat)
            DBSession.flush()

            data = dict(
                success = True,
                id = cat.id,
                name = cat.name,
                slug = cat.slug,
                parent_id = cat.parent_id,
                parent_options = unicode(category_form.c['parent_id'].display()),
                depth = cat.depth(),
                row = unicode(category_row_form.display(
                    action = url_for(id=cat.id),
                    category = cat,
                    depth = cat.depth(),
                    first_child = True,
                )),
            )

        if request.is_xhr:
            return data
        else:
            redirect(action='index', id=None)

    @expose('json')
    def bulk(self, type=None, ids=None, **kwargs):
        """Perform bulk operations on media items

        :param type: The type of bulk action to perform (delete)
        :param ids: A list of IDs.

        """
        if not ids:
            ids = []
        elif not isinstance(ids, list):
            ids = [ids]


        if type == 'delete':
            Category.query.filter(Category.id.in_(ids)).delete(False)
            DBSession.commit()
            success = True
        else:
            success = False

        return dict(
            success = success,
            ids = ids,
            parent_options = unicode(category_form.c['parent_id'].display()),
        )
