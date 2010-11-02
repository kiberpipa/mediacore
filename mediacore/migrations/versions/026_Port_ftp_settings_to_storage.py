import cPickle
import simplejson

from datetime import datetime

from paste.deploy.converters import asbool
from sqlalchemy import *
from sqlalchemy.types import TypeDecorator
from migrate import *

FTP_SERVER = 'ftp_server'
FTP_USERNAME = 'ftp_username'
FTP_PASSWORD = 'ftp_password'
FTP_UPLOAD_DIR = 'ftp_upload_dir'
FTP_MAX_INTEGRITY_RETRIES = 'ftp_max_integrity_retries'
HTTP_DOWNLOAD_URI = 'http_download_uri'
RTMP_SERVER_URI = 'rtmp_server_uri'

class Json(TypeDecorator):
    impl = Text

    def process_bind_param(self, value, dialect):
        return simplejson.dumps(value)

    def process_result_value(self, value, dialect):
        return simplejson.loads(value)

metadata = MetaData()
settings = Table('settings', metadata,
    Column('id', Integer, autoincrement=True, primary_key=True),
    Column('key', Unicode(255), nullable=False, unique=True),
    Column('value', UnicodeText),
    mysql_engine='InnoDB',
    mysql_charset='utf8',
)
storage = Table('storage', metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('engine_type', Unicode(30), nullable=False),
    Column('display_name', Unicode(100), nullable=False, unique=True),
    Column('data', Json, nullable=False),
    Column('enabled', Boolean, nullable=False, default=True),
    Column('created_on', DateTime, nullable=False, default=datetime.now),
    Column('modified_on', DateTime, nullable=False, default=datetime.now,
                                                    onupdate=datetime.now),
    mysql_engine='InnoDB',
    mysql_charset='utf8',
)

def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind migrate_engine
    # to your metadata
    metadata.bind = migrate_engine
    conn = migrate_engine.connect()

    # Grab the current ftp settings
    ftp_settings = {}
    query = select([settings.c.key, settings.c.value],
                   settings.c.key.startswith('ftp_'))
    for key, value in conn.execute(query):
        ftp_settings[key] = value

    # If the ftp settings have changed, copy them to a storage engine
    if ftp_settings['ftp_server'] != 'ftp.someserver.com':
        display_name = ftp_settings['ftp_server']
        if not display_name.startswith('ftp'):
            display_name = 'FTP: %s' % display_name
        conn.execute(storage.insert().values(
            engine_type=u'FTPStorage',
            display_name=display_name,
            enabled=asbool(ftp_settings['ftp_storage']),
            data={
                FTP_SERVER: ftp_settings['ftp_server'],
                FTP_USERNAME: ftp_settings['ftp_user'],
                FTP_PASSWORD: ftp_settings['ftp_password'],
                FTP_UPLOAD_DIR: ftp_settings['ftp_upload_directory'],
                FTP_MAX_INTEGRITY_RETRIES: int(ftp_settings['ftp_upload_integrity_retries']),
                HTTP_DOWNLOAD_URI: ftp_settings['ftp_download_url'],
                RTMP_SERVER_URI: '',
            }
        ))

    query = settings.delete().where(settings.c.key.in_([
        'ftp_storage',
        'ftp_server',
        'ftp_user',
        'ftp_password',
        'ftp_upload_directory',
        'ftp_upload_integrity_retries',
        'ftp_download_url',
    ]))
    conn.execute(query)

def downgrade(migrate_engine):
    raise NotImplementedError()
