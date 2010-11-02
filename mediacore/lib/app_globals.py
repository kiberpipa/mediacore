"""The application's Globals object"""

from beaker.cache import CacheManager
from beaker.util import parse_cache_config_options

class Globals(object):
    """Globals acts as a container for objects available throughout the
    life of the application

    """
    def __init__(self, config):
        """One instance of Globals is created during application
        initialization and is available during requests via the
        'app_globals' variable

        """
        self.cache = cache = CacheManager(**parse_cache_config_options(config))
        self.settings_cache = cache.get_cache('app_settings',
                                              expire=3600,
                                              type='memory')

    @property
    def settings(self):
        def fetch_settings():
            from mediacore.model import DBSession, Setting
            settings_dict = dict(DBSession.query(Setting.key, Setting.value))
            return settings_dict
        return self.settings_cache.get(createfunc=fetch_settings, key=None)
