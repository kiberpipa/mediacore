import logging
import urllib2
import urlparse
from datetime import date, datetime

from pytz import timezone, utc
from icalendar import Calendar
from babel.dates import format_datetime
from pylons import request, response, session, tmpl_context as c, app_globals as g, url
from pylons.controllers.util import abort, redirect
from pylons.decorators.cache import beaker_cache

from mediacore.lib.base import BaseController
from mediacore.lib.decorators import expose, validate

log = logging.getLogger(__name__)

class KiberpipaController(BaseController):

    @beaker_cache(expire=600, type='memory')
    @expose('live.html')
    def live(self, **kw):
        number_of_events_displayed = 10
        cortado_url = g.settings['live_cortado_url']
        # TODO: l10n, locale
        tz = timezone('Europe/Ljubljana')
        locale = 'sl_SI'

        # check if stream is online
        try:
            f = urllib2.urlopen(g.settings['live_stream_url'])
        except urllib2.HTTPError:
            is_live = False
        else:
            is_live = True
            f.close()

        # parse kiberpipa events rss
        events = []
        try:
            f = urllib2.urlopen(g.settings['live_ical_url'])
        except urllib2.HTTPError:
            pass
        else:
            try:
                cal = Calendar.from_string(f.read())
            finally:
                f.close()

            for event in cal.walk()[1:]:
                d = event['DTSTART'].dt
                start_date = datetime(d.year, d.month, d.day, d.hour, d.minute, d.second, tzinfo=utc)
                # leave out events in the past
                if date.today() > date(start_date.year, start_date.month, start_date.day):
                    continue
                events.append({
                    'title': event['SUMMARY'],
                    'link': urlparse.urljoin('http://www.kiberpipa.org/', event['URL']),
                    'start_date': start_date,
                    'location': event['LOCATION'],
                })
                if len(events) == number_of_events_displayed:
                    break

            # sort by date
            events = sorted(events, key=lambda x: x['start_date'])

        return {
            'cortado_url': cortado_url,
            'is_live': is_live,
            'events': events,
            'format_datetime': format_datetime,
            'tz': tz,
            'locale': locale,
        }
