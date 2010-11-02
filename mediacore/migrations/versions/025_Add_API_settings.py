from sqlalchemy import *
from migrate import *

SETTINGS = [
    (u'api_secret_key_required', u'false'),
    (u'api_secret_key', u''),
    (u'api_media_max_results', u'50'),
    (u'api_tree_max_depth', u'10'),
]

metadata = MetaData()
settings = Table('settings', metadata,
    Column('id', Integer, autoincrement=True, primary_key=True),
    Column('key', Unicode(255), nullable=False, unique=True),
    Column('value', UnicodeText),
    mysql_engine='InnoDB',
    mysql_charset='utf8',
)

def upgrade(migrate_engine):
    metadata.bind = migrate_engine
    for key, value in SETTINGS:
        query = settings.insert().values(key=key, value=value)
        migrate_engine.execute(query)

def downgrade(migrate_engine):
    metadata.bind = migrate_engine
    for key, value in SETTINGS:
        query = settings.delete().where(settings.c.key == key)
        migrate_engine.execute(query)
