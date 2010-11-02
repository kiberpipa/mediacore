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
from paste.util import mimeparse
from pylons import config, request, response, session, tmpl_context as c
from sqlalchemy import orm, sql

from mediacore.lib.base import BaseController
from mediacore.lib.decorators import (beaker_cache, expose, expose_xhr,
    observable, paginate, validate)
from mediacore.lib.helpers import get_featured_category, redirect, url_for
from mediacore.model import Category, Media, Podcast, fetch_row
from mediacore.model.meta import DBSession
from mediacore.plugin import events

import logging
from paste.util import mimeparse
log = logging.getLogger(__name__)

class CategoriesController(BaseController):
    """
    Categories Controller

    Handles the display of the category hierarchy, displaying the media
    associated with any given category and its descendants.

    """

    def __before__(self, *args, **kwargs):
        """Load all our category data before each request."""
        BaseController.__before__(self, *args, **kwargs)

        c.categories = Category.query.order_by(Category.name).populated_tree()

        counts = dict(DBSession.query(Category.id,
                                      Category.media_count_published))
        c.category_counts = counts.copy()
        for cat, depth in c.categories.traverse():
            count = counts[cat.id]
            if count:
                for ancestor in cat.ancestors():
                    c.category_counts[ancestor.id] += count

        category_slug = request.environ['pylons.routes_dict'].get('slug', None)
        if category_slug:
            c.category = fetch_row(Category, slug=category_slug)
            c.breadcrumb = c.category.ancestors()
            c.breadcrumb.append(c.category)

    @expose('categories/index.html')
    @observable(events.CategoriesController.index)
    def index(self, slug=None, **kwargs):
        media = Media.query.published()\
            .options(orm.undefer('comment_count_published'))

        if c.category:
            media = media.in_category(c.category)

        latest = media.order_by(Media.publish_on.desc())
        popular = media.order_by(Media.popularity_points.desc())
        featured = None

        featured_cat = get_featured_category()
        if featured_cat:
            featured = latest.in_category(featured_cat).first()
        if not featured:
            featured = popular.first()

        latest = latest.exclude(featured)[:5]
        popular = popular.exclude(latest, featured)[:5]

        return dict(
            featured=featured,
            latest=latest,
            popular=popular,
        )

    @expose('categories/more.html')
    @paginate('media', items_per_page=20)
    @observable(events.CategoriesController.more)
    def more(self, slug, order, page=1, **kwargs):
        media = Media.query.published()\
            .options(orm.undefer('comment_count_published'))\
            .in_category(c.category)

        if order == 'latest':
            media = media.order_by(Media.publish_on.desc())
        else:
            media = media.order_by(Media.popularity_points.desc())

        return dict(
            media = media,
            order = order,
        )

    @beaker_cache(expire=60 * 60 * 4, query_args=True)
    @expose("sitemaps/mrss.xml")
    def feed(self, limit=30, **kwargs):
        """ Generate a media rss feed of the latest media

        :param limit: the max number of results to return. Defaults to 30

        """
        response.content_type = mimeparse.best_match(
            ['application/rss+xml', 'application/xml', 'text/xml'],
            request.environ.get('HTTP_ACCEPT', '*/*')
        )

        media = Media.query.published()

        if c.category:
            media = media.in_category(c.category)

        media = media.order_by(Media.publish_on.desc()).limit(limit)

        return dict(
            media = media,
            title = u'%s Media' % c.category.name,
        )
