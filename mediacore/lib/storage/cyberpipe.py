#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import logging
from shutil import copyfileobj

from pylons import config
from pylons.i18n import N_

from mediacore.lib.storage import LocalFileStorage
from mediacore.forms.admin.storage.localfiles import LocalFileStorageForm
from mediacore.lib.storage import FileStorageEngine, safe_file_name

log = logging.getLogger(__name__)

class CyberpipeLocalFileStorage(LocalFileStorage):
    """docstring for CyberpipeFileStorage"""

    engine_type = "CyberpipeFileStorage"

    default_name = N_(u'Cyberpipe Local File Storage')

    _default_data = {
        'path': '/home/arhivar/static_html/media/',
        'rtmp_server_uri': None,
    }
    # TODO: parse birate, width, height, display_name

    def _get_path(self, media_file):
        """return the local file path for the given unique id.

        this method is exclusive to this engine.
        """
        path = self.folder(media_file)
        if not os.path.exists(path):
            os.mkdir(path)
        return os.path.join(path, media_file.unique_id)

    def folder(self, media_file, slug=None):
        """Return folder where media_file is located"""
        basepath = self._data.get('path', config.get('media_dir', None))
        return os.path.join(basepath, slug or media_file.media.slug)

FileStorageEngine.register(CyberpipeLocalFileStorage)
