#!/usr/bin/env python2.6
# -*- coding: utf-8 -*-
from mediacore.lib.commands import LoadAppCommand, load_app

_script_name = "Kiberpipas convert command from old video archive"
_script_description = \
"""Use this script to create new MediaCore podcasts from old arhive.

"""

DEBUG = False

if __name__ == "__main__":
    cmd = LoadAppCommand(_script_name, _script_description)
    cmd.parser.add_option('--debug', action='store_true', dest='debug', help='Write debug output to STDOUT.', default=False)
    load_app(cmd)
    DEBUG = cmd.options.debug

# BEGIN SCRIPT & SCRIPT SPECIFIC IMPORTS
import pdb
import sys
import re
import os
import urllib2
import urlparse
import tempfile
import shutil
from datetime import datetime
import logging

from mediacore.model import Author, Media, MediaFile, Category, slugify
from mediacore.model.storage import StorageEngine
from mediacore.model.media import MediaMeta
from mediacore.model.meta import DBSession
from mediacore.lib.helpers import duration_to_seconds
from mediacore.lib.thumbnails import create_default_thumbs_for, create_thumbs_for
from mediacore.lib.mediafiles import attach_and_store_media_file, media_file_from_filename
from mediacore.lib.filetypes import VIDEO

storage_id = DBSession.query(StorageEngine).filter(StorageEngine.display_name=='Cyberpipe Local File Storage').one().id

def create_media(e):
    """Media info:

videos.append({
  'video_id' : u'WCLJ_Tomaz_Stolfa-The_Internet_of_Things',
  'title' : u'The Internet of Things',
  'authors': [ u'Tomaž Štolfa' ],
  'date': u'28.11.2009',
  'duration' : u'00:24:48',
  'categories': [u'Web Camp Ljubljana', u'*camp events', u'English content'] ,
  'video' : u'/home/arhivar/static_html/media/WCLJ_Tomaz_Stolfa-The_Internet_of_Things/video.ogg',
  'image': u'/home/arhivar/static_html/media/WCLJ_Tomaz_Stolfa-The_Internet_of_Things/image.jpg',
  'format' : u'ogg',
  'primary' : {
    'file' : u'/home/arhivar/static_html/media/WCLJ_Tomaz_Stolfa-The_Internet_of_Things/video.ogg',
    'format': u'ogg',
    'codec' : u'theora',
    'width' : 768,
    'height' : 576,
    'aspect' : u'4:3',
    'duration' : u'00:24:48' },
  'secondaries' : [ {
    'file' : u'/home/arhivar/static_html/media/WCLJ_Tomaz_Stolfa-The_Internet_of_Things/video.webm',
    'format': u'webm',
    'codec' : u'libvpx_vp8',
    'width' : 768,
    'height' : 576,
    'aspect' : u'4:3',
    'duration' : u'00:24:48' }, ],
  'extras' : {
    u'url' : 'http://www.webcamp.si/',
    u'cat' : 'camp english',
    u'published' : '28.11.2009',
    u'desc' : 'The Internet of Things - inspired by The Internet of Stuff by Alexandra Sonsino'}
})

    """
    author_name = u"arhivar"
    author_email = u"video@kiberpipa.org"
    date_format = '%d.%m.%Y'

    categories = []
    tmp = e['duration'].split(':')
    duration = int(tmp[0])*60*60 + int(tmp[1])*60 + int(tmp[2])

    # create categories if not in db
    for category in e['categories']:
        cat = DBSession.query(Category).filter(Category.name == category).first()
        if not cat:
            cat = Category(name=category, slug=slugify(category))
            DBSession.add(cat)
            DBSession.flush()
        categories.append(cat.id)

    media = Media()
    media.slug = e['video_id']
    media.title = e['title']
    media.type = VIDEO
    media.author = Author(author_name, author_email)
    media.description = e['extras'].get('desc', None)
    media.set_categories(categories)
    media.publish_on = datetime.strptime(e['extras']['published'], date_format)
    media.created_on = datetime.strptime(e['date'], date_format)
    media.publishable = True
    media.reviewed = True
    media.encoded = True
    media.duration = duration

    DBSession.add(media)
    DBSession.flush()

    # URL for media
    if 'url' in e['extras']:
        media.meta['URL'] = value=e['extras']['url']

    # authors
    media.meta['authors'] = ", ".join(e['authors'])

    # Create thumbs from image, or default thumbs
    create_thumbs_for(media, open(e['image']), e['video_id'] + '.jpg')

    e['secondaries'].append(e['primary'])

    for video_info in e['secondaries']:
        media_file = MediaFile()
        # name of download file
        media_file.unique_id = os.path.basename(video_info['file'])
        media_file.width = video_info['width']
        media_file.height = video_info['height']
        media_file.container = video_info['format']
        media_file.display_name = "%s.%s" % (slugify(media.title), media_file.container)
        media_file.size = os.stat(video_info['file'])[6]
        media_file.type = VIDEO
        if 'bitrate' in video_info:
            media_file.bitrate = video_info['bitrate']
        media_file.media = media
        media_file.storage_id = storage_id
        DBSession.add(media_file)
        DBSession.flush()

    media.update_status()

    return media


def main(parser, options, args):
    import data

    for video in data.videos:
        try:
            create_media(video)
            DBSession.commit()
        except Exception, e:
            DBSession.rollback()
            logging.exception(e)

if __name__ == "__main__":
    main(cmd.parser, cmd.options, cmd.args)
