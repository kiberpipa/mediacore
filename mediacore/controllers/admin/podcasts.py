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

import os.path
import shutil

from pylons import config, request, response, session, tmpl_context
from repoze.what.predicates import has_permission
from sqlalchemy import orm, sql

from mediacore.forms.admin import SearchForm, ThumbForm
from mediacore.forms.admin.podcasts import PodcastForm
from mediacore.lib import helpers
from mediacore.lib.base import BaseController
from mediacore.lib.decorators import expose, expose_xhr, observable, paginate, validate
from mediacore.lib.helpers import redirect, url_for
from mediacore.lib.thumbnails import thumb_paths, create_thumbs_for, create_default_thumbs_for
from mediacore.model import Author, AuthorWithIP, Podcast, fetch_row, get_available_slug
from mediacore.model.meta import DBSession
from mediacore.plugin import events

import logging
log = logging.getLogger(__name__)

podcast_form = PodcastForm()
thumb_form = ThumbForm()

class PodcastsController(BaseController):
    allow_only = has_permission('edit')

    @expose_xhr('admin/podcasts/index.html',
                'admin/podcasts/index-table.html')
    @paginate('podcasts', items_per_page=10)
    @observable(events.Admin.PodcastsController.index)
    def index(self, page=1, **kw):
        """List podcasts with pagination.

        :param page: Page number, defaults to 1.
        :type page: int
        :rtype: Dict
        :returns:
            podcasts
                The list of :class:`~mediacore.model.podcasts.Podcast`
                instances for this page.
        """
        podcasts = DBSession.query(Podcast)\
            .options(orm.undefer('media_count'))\
            .order_by(Podcast.title)
        return dict(podcasts=podcasts)


    @expose('admin/podcasts/edit.html')
    @observable(events.Admin.PodcastsController.edit)
    def edit(self, id, **kwargs):
        """Display the podcast forms for editing or adding.

        This page serves as the error_handler for every kind of edit action,
        if anything goes wrong with them they'll be redirected here.

        :param id: Podcast ID
        :type id: ``int`` or ``"new"``
        :param \*\*kwargs: Extra args populate the form for ``"new"`` podcasts
        :returns:
            podcast
                :class:`~mediacore.model.podcasts.Podcast` instance
            form
                :class:`~mediacore.forms.admin.podcasts.PodcastForm` instance
            form_action
                ``str`` form submit url
            form_values
                ``dict`` form values
            thumb_form
                :class:`~mediacore.forms.admin.ThumbForm` instance
            thumb_action
                ``str`` form submit url

        """
        podcast = fetch_row(Podcast, id)

        if tmpl_context.action == 'save' or id == 'new':
            form_values = kwargs
            user = request.environ['repoze.who.identity']['user']
            form_values.setdefault('author_name', user.display_name)
            form_values.setdefault('author_email', user.email_address)
            form_values.setdefault('feed', {}).setdefault('feed_url',
                u'Save the podcast to get your feed URL')
        else:
            explicit_values = {True: 'yes', False: 'clean', None: 'no'}
            form_values = dict(
                slug = podcast.slug,
                title = podcast.title,
                subtitle = podcast.subtitle,
                author_name = podcast.author and podcast.author.name or None,
                author_email = podcast.author and podcast.author.email or None,
                description = podcast.description,
                details = dict(
                    explicit = explicit_values.get(podcast.explicit),
                    category = podcast.category,
                    copyright = podcast.copyright,
                ),
                feed = dict(
                    feed_url = url_for(controller='/podcasts', action='feed',
                                       slug=podcast.slug, qualified=True),
                    itunes_url = podcast.itunes_url,
                    feedburner_url = podcast.feedburner_url,
                ),
            )

        return dict(
            podcast = podcast,
            form = podcast_form,
            form_action = url_for(action='save'),
            form_values = form_values,
            thumb_form = thumb_form,
            thumb_action = url_for(action='save_thumb'),
        )


    @expose()
    @validate(podcast_form, error_handler=edit)
    @observable(events.Admin.PodcastsController.save)
    def save(self, id, slug, title, subtitle, author_name, author_email,
             description, details, feed, delete=None, **kwargs):
        """Save changes or create a new :class:`~mediacore.model.podcasts.Podcast` instance.

        Form handler the :meth:`edit` action and the
        :class:`~mediacore.forms.admin.podcasts.PodcastForm`.

        Redirects back to :meth:`edit` after successful editing
        and :meth:`index` after successful deletion.

        """
        podcast = fetch_row(Podcast, id)

        if delete:
            file_paths = thumb_paths(podcast).values()
            DBSession.delete(podcast)
            DBSession.commit()
            helpers.delete_files(file_paths, Podcast._thumb_dir)
            redirect(action='index', id=None)

        if not slug:
            slug = title
        if slug != podcast.slug:
            podcast.slug = get_available_slug(Podcast, slug, podcast)
        podcast.title = title
        podcast.subtitle = subtitle
        podcast.author = Author(author_name, author_email)
        podcast.description = description
        podcast.copyright = details['copyright']
        podcast.category = details['category']
        podcast.itunes_url = feed['itunes_url']
        podcast.feedburner_url = feed['feedburner_url']
        podcast.explicit = {'yes': True, 'clean': False}.get(details['explicit'], None)

        if id == 'new':
            DBSession.add(podcast)
            DBSession.flush()
            create_default_thumbs_for(podcast)

        redirect(action='edit', id=podcast.id)


    @expose('json')
    @validate(thumb_form, error_handler=edit)
    @observable(events.Admin.PodcastsController.save_thumb)
    def save_thumb(self, id, thumb, **values):
        """Save a thumbnail uploaded with :class:`~mediacore.forms.admin.ThumbForm`.

        :param id: Media ID. If ``"new"`` a new Podcast stub is created.
        :type id: ``int`` or ``"new"``
        :param file: The uploaded file
        :type file: :class:`cgi.FieldStorage` or ``None``
        :rtype: JSON dict
        :returns:
            success
                bool
            message
                Error message, if unsuccessful
            id
                The :attr:`~mediacore.model.podcasts.Podcast.id` which is
                important if a new podcast has just been created.

        """
        if id == 'new':
            return dict(
                success = False,
                message = u'You must first save the podcast before you can upload a thumbnail',
            )

        podcast = fetch_row(Podcast, id)

        try:
            # Create JPEG thumbs
            create_thumbs_for(podcast, thumb.file, thumb.filename)
            success = True
            message = None
        except IOError, e:
            success = False
            if e.errno == 13:
                message = 'Permission denied, cannot write file'
            elif e.message == 'cannot identify image file':
                message = 'Unsupport image type: %s' \
                    % os.path.splitext(thumb.filename)[1].lstrip('.')
            else:
                raise

        return dict(
            success = success,
            message = message,
        )
