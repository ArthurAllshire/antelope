import requests
from requests.exceptions import HTTPError
from collections import OrderedDict
from util.data_store import DataStore
import os


class BlueAllianceWrapper():

    TBA_API = 'http://www.thebluealliance.com/api/v3'

    def __init__(self, tba_auth_key):

        self.tba_key = tba_auth_key
        self.headers = {'X-TBA-App-Id': 'Arthur Allshire:Antelope',
                        'X-TBA-Auth-Key': self.tba_key}
        new_ds = not os.path.isfile('cache/data_store.txt')
        if new_ds:
            print('Creating new data store')
            years = range(2008, 2019)
            year_events = {}
            for year in years:
                print('Fetching year events for %s' % year)
                events = self.get_year_events(year)
                year_events[year] = [event['key'] for event in events]
            self.data_store = DataStore(new_data_store=True, year_events=year_events)
        else:
            self.data_store = DataStore()

    def get_year_events(self, year):
        year = str(year) if type(year) is int else year
        request_url = self.TBA_API + "/events/" + year
        events = requests.get(request_url, headers=self.headers)
        try:
            events.raise_for_status()
        except HTTPError:
            print("Attempt to get %s matches failed with HTTP error %s"
                  % (year, events.status_code))
            print("Request URL: %s" % (request_url))
            raise
        events_sorted = sorted(
                events.json(), key=lambda x: x["start_date"])
        return events_sorted

    def is_cached(self, event_code):
        ev_year = int(event_code[:4])
        cached_matches = self.data_store.get_event_matches(ev_year, event_code)
        return cached_matches is not None

    def get_event_matches(self, event_code):
        ev_year = int(event_code[:4])
        cached_matches = self.data_store.get_event_matches(ev_year, event_code)
        if cached_matches is None:
            print("Request made for matches")
            request_url = self.TBA_API + '/event/' + event_code + '/matches'
            matches = requests.get(request_url, headers=self.headers)
            sorted_matches = self.sort_by_match_number(matches.json())
            return sorted_matches
        return cached_matches

    def cache_matches(self, event_code, matches):
        ev_year = int(event_code[:4])
        self.data_store.add_event_matches(ev_year, event_code, matches)

    def get_raw_event(self, event_code):
        request_url = self.TBA_API + '/event/' + event_code
        event = requests.get(request_url, headers=self.headers)
        return event.json()

    def get_year_matches(self, year):
        year = str(year) if type(year) is int else year
        events = self.get_year_events(year)
        event_matches = OrderedDict()
        trust_cache = os.path.isfile('cache/data_store.txt')
        if trust_cache:
            return self.data_store.data[int(year)]
        else:
            for event in events:
                print('Fetching matches for %s' % event['event_code'])
                event_matches[year + event['event_code']] = \
                    self.get_event_matches(year + event['event_code'])

        return event_matches

    def fetch_alliance_data(self, event_code):
        request_url = self.TBA_API + '/event/' + event_code + '/alliances'
        alliance_data = requests.get(request_url, headers=self.headers)
        return alliance_data.json()

    @staticmethod
    def sort_by_match_number(matches):
        """ Sort matches (which is a list of JSON dictionares representing a
        Blue Alliance API event response) by match number """

        comp_levels = OrderedDict()
        comp_levels['qm'] = []
        comp_levels['ef'] = []
        comp_levels['qf'] = []
        comp_levels['sf'] = []
        comp_levels['f'] = []

        for match in matches:
            comp_levels[match['comp_level']].append(match)
        sorted_matches = []
        for level in comp_levels.values():
            sorted_matches += \
                sorted(level,
                       key=lambda x: (x['match_number'], x['set_number']))

        return sorted_matches

    @staticmethod
    def has_match_been_played(match):
        """ Determine if match has been played """
        # TODO: check if this method works
        for alliance in ['blue', 'red']:
            if (match['alliances'][alliance]['score'] is None) or \
               (match['alliances'][alliance]['score'] == -1):
                return False
        return True
