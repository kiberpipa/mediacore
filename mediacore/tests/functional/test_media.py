from mediacore.tests import *
from mediacore.model import *

class TestMediaController(TestController):

    def test_index(self):
        response = self.app.get(url(controller='media', action='index'))
        # Test response...

    def test_no_media(self):
        DBSession.query(Media).delete()
        self.app.get(url(controller='media', action='explore'))
        self.app.get(url(controller='media', action='index'))
