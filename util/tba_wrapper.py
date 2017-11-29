import requests
from requests.exceptions import HTTPError
from collections import OrderedDict


class BlueAllianceWrapper():

    TBA_API = 'http://www.thebluealliance.com/api/v3'

    def __init__(self, tba_auth_key):

        self.tba_key = tba_auth_key
        self.headers = {'X-TBA-App-Id': 'Arthur Allshire:Antelope',
           'X-TBA-Auth-Key': self.tba_key}

    def get_year_events(self, year):
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

    def get_event_matches(self, event_code):
        request_url = self.TBA_API + '/event/' + event_code + '/matches'
        matches = requests.get(request_url, headers=self.headers)
        sorted_matches = self.sort_by_match_number(matches.json())
        return sorted_matches

    def get_raw_event(self, event_code):
        request_url = self.TBA_API + '/event/' + event_code
        event = requests.get(request_url, headers=self.headers)
        return event.json()

    def get_year_matches(self, year):
        events = self.get_year_events(year)
        event_matches = OrderedDict()
        for event in events:
            print(event['event_code'])
            event_matches[year + event['event_code']] = \
                self.get_event_matches(year + event['event_code'])

        return event_matches

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
        """ Determine if match (Match model json) has been played """
        # TODO: check if this method works
        return bool(match['score_breakdown'])
