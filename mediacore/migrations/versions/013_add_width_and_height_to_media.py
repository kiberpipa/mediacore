from sqlalchemy import *
from migrate import *

metadata = MetaData()
width_c = Column('width', Integer)
height_c = Column('height', Integer)

def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind migrate_engine
    # to your metadata
    metadata.bind = migrate_engine
    media = Table('media_files', metadata, autoload=True, autoload_with=migrate_engine)
    width_c.create(media)
    height_c.create(media)

def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    metadata.bind = migrate_engine
    media = Table('media_files', metadata, autoload=True, autoload_with=migrate_engine)
    width_c.drop(media)
    height_c.drop(media)
