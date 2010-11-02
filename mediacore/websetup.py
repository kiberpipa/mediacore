"""Setup the MediaCore application"""
import logging
import os.path
import random
import string

import pylons
import pylons.test
from pylons.i18n import N_
from sqlalchemy.orm import class_mapper
from migrate.versioning.api import (drop_version_control, version_control,
    version, upgrade)
from migrate.versioning.exceptions import DatabaseAlreadyControlledError

from mediacore.config.environment import load_environment
from mediacore.lib.storage import (BlipTVStorage, GoogleVideoStorage,
    LocalFileStorage, RemoteURLStorage, VimeoStorage, YoutubeStorage)
from mediacore.model import (DBSession, metadata, Media, MediaFile, Podcast,
    User, Group, Permission, Tag, Category, Comment, Setting, Author,
    AuthorWithIP)

log = logging.getLogger(__name__)

migrate_repository = 'mediacore/migrations'

def setup_app(command, conf, vars):
    """Called by ``paster setup-app``.

    This script is responsible for:

        * Creating the initial database schema and loading default data.
        * Executing any migrations necessary to bring an existing database
          up-to-date. Your data should be safe but, as always, be sure to
          make backups before using this.
        * Re-creating the default database for every run of the test suite.

    XXX: All your data will be lost IF you run the test suite with a
         config file named 'test.ini'. Make sure you have this configured
         to a different database than in your usual deployment.ini or
         development.ini file because all database tables are dropped a
         and recreated every time this script runs.

    XXX: If you are upgrading from MediaCore v0.7.2 or v0.8.0, run whichever
         one of these that applies:
           ``python batch-scripts/upgrade/upgrade_from_v072.py deployment.ini``
           ``python batch-scripts/upgrade/upgrade_from_v080.py deployment.ini``

    XXX: For search to work, we depend on a number of MySQL triggers which
         copy the data from our InnoDB tables to a MyISAM table for its
         fulltext indexing capability. Triggers can only be installed with
         a mysql superuser like root, so you must run the setup_triggers.sql
         script yourself.

    """
    if pylons.test.pylonsapp:
        # NOTE: This extra filename check may be unnecessary, the example it is
        # from did not check for pylons.test.pylonsapp. Leaving it in for now
        # to make it harder for someone to accidentally delete their database.
        filename = os.path.split(conf.filename)[-1]
        if filename == 'test.ini':
            log.info('Dropping existing tables...')
            metadata.drop_all(checkfirst=True)
            drop_version_control(conf.local_conf['sqlalchemy.url'],
                                 migrate_repository)
    else:
        # Don't reload the app if it was loaded under the testing environment
        config = load_environment(conf.global_conf, conf.local_conf)

    # Create the migrate_version table if it doesn't exist.
    # If the table doesn't exist, we assume the schema was just setup
    # by this script and therefore must be the latest version.
    latest_version = version(migrate_repository)
    try:
        version_control(conf.local_conf['sqlalchemy.url'],
                        migrate_repository,
                        version=latest_version)
    except DatabaseAlreadyControlledError:
        log.info('Running any new migrations, if there are any')
        upgrade(conf.local_conf['sqlalchemy.url'],
                migrate_repository,
                version=latest_version)
    else:
        log.info('Initializing new database with version %r' % latest_version)
        metadata.create_all(bind=DBSession.bind, checkfirst=True)
        add_default_data()

    # Save everything, along with the dummy data if applicable
    DBSession.commit()
    log.info('Successfully setup')

def random_string(length):
    return u"".join([random.choice(string.letters+string.digits) for x in range(1, length)])

def add_default_data():
    log.info('Adding default data')

    settings = [
        (u'email_media_uploaded', None),
        (u'email_comment_posted', None),
        (u'email_support_requests', None),
        (u'email_send_from', u'noreply@localhost'),
        (u'wording_user_uploads', N_(u"Upload your media using the form below. We'll review it and get back to you.")),
        (u'wording_additional_notes', None),
        (u'popularity_decay_exponent', u'4'),
        (u'popularity_decay_lifetime', u'36'),
        (u'rich_text_editor', u'tinymce'),
        (u'google_analytics_uacct', u''),
        (u'flash_player', u'jwplayer'),
        (u'html5_player', u'html5'),
        (u'player_type', u'best'),
        (u'featured_category', u'1'),
        (u'max_upload_size', u'314572800'),
        (u'ftp_storage', u'false'),
        (u'ftp_server', u'ftp.someserver.com'),
        (u'ftp_user', u'username'),
        (u'ftp_password', u'password'),
        (u'ftp_upload_directory', u'media'),
        (u'ftp_download_url', u'http://www.someserver.com/web/accessible/media/'),
        (u'ftp_upload_integrity_retries', u'10'),
        (u'akismet_key', u''),
        (u'akismet_url', u''),
        (u'req_comment_approval', u'false'),
        (u'use_embed_thumbnails', u'true'),
        (u'api_secret_key_required', u'true'),
        (u'api_secret_key', random_string(20)),
        (u'api_media_max_results', u'50'),
        (u'api_tree_max_depth', u'10'),
        (u'live_stream_url', u'http://kiberpipa.org:8000/kiberpipa.ogg'),
        (u'live_ical_url', u'http://www.kiberpipa.org/calendar/ical/'),
        (u'live_cortado_url', u'/cortado-ovt-stripped.jar'),
        (u'ldap_connection', u'ldap://localhost/'),
        (u'ldap_dn', u'ou=People,dc=kiberpipa,dc=org'),
    ]

    for key, value in settings:
        s = Setting()
        s.key = key
        s.value = value
        DBSession.add(s)

    u = User()
    u.user_name = u'admin'
    u.display_name = u'Admin'
    u.email_address = u'admin@somedomain.com'
    u.password = u'admin'
    DBSession.add(u)

    g = Group()
    g.group_name = u'admins'
    g.display_name = u'Admins'
    g.users.append(u)
    DBSession.add(g)

    p = Permission()
    p.permission_name = u'admin'
    p.description = u'Grants access to the admin panel'
    p.groups.append(g)
    DBSession.add(p)

    remote_url_storage = RemoteURLStorage()
    default_engines = [
        LocalFileStorage(),
        remote_url_storage,
        YoutubeStorage(),
        VimeoStorage(),
        BlipTVStorage(),
        GoogleVideoStorage(),
    ]
    for engine in default_engines:
        DBSession.add(engine)

