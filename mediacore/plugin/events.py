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
"""
Abstract events which plugins subscribe to and are called by the app.
"""
import logging

from sqlalchemy.orm.interfaces import MapperExtension

log = logging.getLogger(__name__)

class Event(object):
    """
    An arbitrary event that's triggered and observed by different parts of the app.

        >>> e = Event()
        >>> e.observers.append(lambda x: x)
        >>> e('x')

    """
    def __init__(self, args):
        self.args = args and tuple(args) or None
        self.observers = []

    def __call__(self, *args, **kwargs):
        for observer in self.observers:
            observer(*args, **kwargs)

    def __iter__(self):
        return iter(self.observers)

class GeneratorEvent(Event):
    """
    An arbitrary event that yields all results from all observers.
    """
    def __call__(self, *args, **kwargs):
        for observer in self.observers:
            for result in observer(*args, **kwargs):
                yield result

class observes(object):
    """
    Register the decorated function as an observer of the given event.
    """
    def __init__(self, *events):
        self.events = events

    def __call__(self, func):
        for event in self.events:
            event.observers.append(func)
        return func

class MapperObserver(MapperExtension):
    """
    Fire events whenever the mapper triggers any kind of row modification.
    """
    def __init__(self, event_group):
        self.event_group = event_group

    def after_delete(self, mapper, connection, instance):
        self.event_group.after_delete(instance)

    def after_insert(self, mapper, connection, instance):
        self.event_group.after_insert(instance)

    def after_update(self, mapper, connection, instance):
        self.event_group.after_update(instance)

    def before_delete(self, mapper, connection, instance):
        self.event_group.before_delete(instance)

    def before_insert(self, mapper, connection, instance):
        self.event_group.before_insert(instance)

    def before_update(self, mapper, connection, instance):
        self.event_group.before_update(instance)

###############################################################################
# Application Setup

class Environment(object):
    routes = Event(['mapper'])
    init_model = Event([])
    loaded = Event(['config'])

###############################################################################
# Controllers

class Admin(object):

    class CategoriesController(object):
        index = Event(['**kwargs'])
        edit = Event(['**kwargs'])
        save = Event(['**kwargs'])

    class CommentsController(object):
        index = Event(['**kwargs'])
        save_status = Event(['**kwargs'])
        save_edit = Event(['**kwargs'])

    class IndexController(object):
        index = Event(['**kwargs'])
        media_table = Event(['**kwargs'])

    class MediaController(object):
        index = Event(['**kwargs'])
        edit = Event(['**kwargs'])
        save = Event(['**kwargs'])
        add_file = Event(['**kwargs'])
        edit_file = Event(['**kwargs'])
        merge_stubs = Event(['**kwargs'])
        save_thumb = Event(['**kwargs'])
        update_status = Event(['**kwargs'])

    class PodcastsController(object):
        index = Event(['**kwargs'])
        edit = Event(['**kwargs'])
        save = Event(['**kwargs'])
        save_thumb = Event(['**kwargs'])

    class TagsController(object):
        index = Event(['**kwargs'])
        edit = Event(['**kwargs'])
        save = Event(['**kwargs'])

    class UsersController(object):
        index = Event(['**kwargs'])
        edit = Event(['**kwargs'])
        save = Event(['**kwargs'])
        delete = Event(['**kwargs'])

class API(object):
    class MediaController(object):
        index = Event(['**kwargs'])
        get = Event(['**kwargs'])

class CategoriesController(object):
    index = Event(['**kwargs'])
    more = Event(['**kwargs'])

class ErrorController(object):
    document = Event(['**kwargs'])
    report = Event(['**kwargs'])

class LoginController(object):
    login = Event(['**kwargs'])
    login_handler = Event(['**kwargs'])
    logout_handler = Event(['**kwargs'])
    post_login = Event(['**kwargs'])
    post_logout = Event(['**kwargs'])

class MediaController(object):
    index = Event(['**kwargs'])
    comment = Event(['**kwargs'])
    explore = Event(['**kwargs'])
    embed_player = Event(['xhtml'])
    jwplayer_rtmp_mrss = Event(['**kwargs'])
    rate = Event(['**kwargs'])
    view = Event(['**kwargs'])

class PodcastsController(object):
    index = Event(['**kwargs'])
    view = Event(['**kwargs'])
    feed = Event(['**kwargs'])

class UploadController(object):
    index = Event(['**kwargs'])
    submit = Event(['**kwargs'])
    submit_async = Event(['**kwargs'])
    success = Event(['**kwargs'])
    failure = Event(['**kwargs'])

###############################################################################
# Models

class Media(object):
    before_delete = Event(['instance'])
    after_delete = Event(['instance'])
    before_insert = Event(['instance'])
    after_insert = Event(['instance'])
    before_update = Event(['instance'])
    after_update = Event(['instance'])

class MediaFile(object):
    before_delete = Event(['instance'])
    after_delete = Event(['instance'])
    before_insert = Event(['instance'])
    after_insert = Event(['instance'])
    before_update = Event(['instance'])
    after_update = Event(['instance'])

class Podcast(object):
    before_delete = Event(['instance'])
    after_delete = Event(['instance'])
    before_insert = Event(['instance'])
    after_insert = Event(['instance'])
    before_update = Event(['instance'])
    after_update = Event(['instance'])

class Comment(object):
    before_delete = Event(['instance'])
    after_delete = Event(['instance'])
    before_insert = Event(['instance'])
    after_insert = Event(['instance'])
    before_update = Event(['instance'])
    after_update = Event(['instance'])

class Category(object):
    before_delete = Event(['instance'])
    after_delete = Event(['instance'])
    before_insert = Event(['instance'])
    after_insert = Event(['instance'])
    before_update = Event(['instance'])
    after_update = Event(['instance'])

class Tag(object):
    before_delete = Event(['instance'])
    after_delete = Event(['instance'])
    before_insert = Event(['instance'])
    after_insert = Event(['instance'])
    before_update = Event(['instance'])
    after_update = Event(['instance'])

class Setting(object):
    before_delete = Event(['instance'])
    after_delete = Event(['instance'])
    before_insert = Event(['instance'])
    after_insert = Event(['instance'])
    before_update = Event(['instance'])
    after_update = Event(['instance'])

class MultiSetting(object):
    before_delete = Event(['instance'])
    after_delete = Event(['instance'])
    before_insert = Event(['instance'])
    after_insert = Event(['instance'])
    before_update = Event(['instance'])
    after_update = Event(['instance'])

class User(object):
    before_delete = Event(['instance'])
    after_delete = Event(['instance'])
    before_insert = Event(['instance'])
    after_insert = Event(['instance'])
    before_update = Event(['instance'])
    after_update = Event(['instance'])

###############################################################################
# Forms

PostCommentForm = Event(['form'])
UploadForm = Event(['form'])
Admin.CategoryForm = Event(['form'])
Admin.CategoryRowForm = Event(['form'])
Admin.EditCommentForm = Event(['form'])
Admin.MediaForm = Event(['form'])
Admin.AddFileForm = Event(['form'])
Admin.EditFileForm = Event(['form'])
Admin.UpdateStatusForm = Event(['form'])
Admin.SearchForm = Event(['form'])
Admin.PodcastForm = Event(['form'])
Admin.PodcastFilterForm = Event(['form'])
Admin.UserForm = Event(['form'])
Admin.TagForm = Event(['form'])
Admin.TagRowForm = Event(['form'])
Admin.ThumbForm = Event(['form'])

###############################################################################
# Miscellaneous... may require refactoring

plugin_settings_links = GeneratorEvent([])
EncodeMediaFile = Event(['media_file'])
