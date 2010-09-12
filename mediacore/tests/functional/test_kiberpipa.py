from mediacore.tests import *

class TestKiberpipaController(TestController):

    def test_live(self):
        response = self.app.get(url(controller='kiberpipa', action='live'))
        self.assertTrue("Live stream" in response.ubody)
        self.assertTrue("no stream running" in response.ubody)
