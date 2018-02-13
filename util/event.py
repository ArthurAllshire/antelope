from datetime import datetime, timedelta
from pytz import timezone, utc
from collections import OrderedDict

import time


class Event:
    """Used to represent an individual event. Stores status information,
    and fetches additional information about other events."""

    # numbers are bracket numbers, others are weird bracket types
    PLAYOFF_TYPE_MAPPING = {0: 8, 1: 16, 2: 4, 4: '6-team-round-robin',
                            5: 'DOUBLE_ELIM_8_TEAM', 6: 'BO5_FINALS'}

    class States:
        NO_DATA = -1  # event has been played, but no data on TBA
        NOT_STARTED = 0  # before start date
        PRE_MATCHES = 1  # after start date, before schedule posted
        MATCHES_POSTED = 2  # schedule posted, no matches
        QUALIFICATION_MATCHES = 3  # quals in progress
        FINAL_MATCHES = 4  # finals in progress
        FINISHED = 5  # all matches played

    StateStrings = {
            States.NO_DATA: "No match data available",
            States.NOT_STARTED: "Before event start",
            States.MATCHES_POSTED: "Schedule posted",
            States.QUALIFICATION_MATCHES: "Qualifications",
            States.FINAL_MATCHES: "Knockout Rounds",
            States.FINISHED: "Event Over"}

    COMP_LEVELS_VERBOSE = {
        "qm": "Quals",
        "ef": "Eighths",
        "qf": "Quarters",
        "sf": "Semis",
        "f": "Finals",
    }

    def __init__(self, event_code, elo, tba_wrapper):
        self.event_code = event_code
        self.elo = elo
        self.tba_wrapper = tba_wrapper
        self.last_status_tm = 0.0
        self.status = None
        self.processed_matches = set()
        self.played_matches = set()
        self.retrodictions = []
        self.upcoming_matches = []

        self.update_event_status()
        if self.status == self.States.FINISHED and not self.tba_wrapper.is_cached(self.event_code):
            print("Caching %s" % self.event_code)
            self.tba_wrapper.cache_matches(self.event_code, self.matches)

    def update_event_status(self):
        update_status = (time.time()-self.last_status_tm) >= 180
        if not update_status:
            return
        last_in_progress = self.in_progress
        # TODO: handle exceptions in the following (ie if no response)
        print("Fetching metadata for %s" % (self.event_code))
        self.event_response = self.tba_wrapper.get_raw_event(self.event_code)
        self.parse_event_response()

        event_dict = {}
        event_dict['start_year'] = str(self.event_start.year)
        event_dict['start_date'] = self.event_start.strftime('%d %b')
        event_dict['end_date'] = self.event_end.strftime('%d %b')
        event_dict['name'] = self.event_response['name']
        event_dict['event_code'] = self.event_code

        matches = self.get_matches()

        update_ratings = self.set_status_code(matches)
        upcoming_matches = self.update_processed_matches(matches)

        event_dict['upcoming_matches'] = upcoming_matches.values()
        event_dict['retrodictions'] = self.retrodictions

        if update_ratings:
            pass

        event_dict['status'] = Event.StateStrings[self.status]
        # TODO: implement finals in progress or not
        event_dict['finals'] = {'in_progress': False}
        event_dict['status_code'] = ('qm'
                                     if self.status == Event.States.QUALIFICATION_MATCHES
                                     else ('fm' if self.status == Event.States.FINAL_MATCHES
                                           else 'none'))

        self.matches = matches
        if (not self.in_progress and last_in_progress):
            self.tba_wrapper.cache_matches(self.event_code, matches)
            print("Caching %s" % self.event_code)
        # This ***MUST*** be done in one step, otherwise we risk sending a user
        # a half completed dictionary.
        self.event_dict = event_dict
        self.last_status_tm = time.time()

    def parse_event_response(self):
        if self.event_response['timezone']:
            # adjust event start/end based on timezone if available
            tz = timezone(self.event_response['timezone'])
        else:
            tz = timezone('UTC')
        self.event_start = tz.localize(
                         datetime.strptime(
                             self.event_response['start_date'], '%Y-%m-%d'))

        self.event_end = tz.localize(
                         datetime.strptime(
                             self.event_response['end_date'], '%Y-%m-%d'))

        # TODO: add support for different round types
        self.teams_in_bracket = 8

    def match_processed(self, match):
        if match['key'] in self.processed_matches:
            return True
        return False

    def process_match(self, match):
        """ Updatpe Elo rating system based on match, and add it to our list of processed
        matches """
        if not self.match_processed(match):
            self.elo.update(match)
            self.processed_matches.add(match['key'])

    def update_processed_matches(self, matches):
        # Assumes matches is sorted by match number!
        unplayed_matches = []
        for match_num, match in enumerate(matches):
            if not self.tba_wrapper.has_match_been_played(match):
                unplayed_matches.append(match)
            else:
                self.update_retrodictions(match)
                self.process_match(match)
        if (not unplayed_matches) or self.status == Event.States.FINISHED:
            return OrderedDict()
        upcoming_matches = OrderedDict()
        for match in unplayed_matches:
            upcoming_matches[match['key']] = \
                self.generate_prediction_dict(match)
        return upcoming_matches

    def generate_prediction_dict(self, match):
        dict = {}
        dict['name'] = \
            "%s %s Match %s" % \
            (self.COMP_LEVELS_VERBOSE[match['comp_level']],
             match['set_number'], match['match_number'])
        for alliance in ['blue', 'red']:
            dict[alliance+'_alliance'] = [team_num.lstrip('frc') for team_num in
                                          match['alliances'][alliance]['team_keys']]
        blue_win_prob = self.elo.predict(match)
        dict['blue_win_prob'] = int(blue_win_prob*100)
        dict['red_win_prob'] = int((1-blue_win_prob)*100)
        dict['predicted_margin'] = int(self.elo.predict_margin(match))
        return dict

    def generate_retrodiction_dict(self, match):
        dict = self.generate_prediction_dict(match)
        dict['actual_margin'] = int(match['alliances']['blue']['score']
                                    - match['alliances']['red']['score'])
        return dict

    def update_retrodictions(self, match):
        if not match['key'] in self.played_matches:
            self.retrodictions.append(self.generate_retrodiction_dict(match))
            self.played_matches.add(match['key'])

    def get_matches(self):
        print("Fetching match data for %s" % (self.event_code))
        matches = self.tba_wrapper.get_event_matches(self.event_code)
        return matches

    @property
    def in_progress(self):
        return self.status in [Event.States.QUALIFICATION_MATCHES,
                               Event.States.FINAL_MATCHES]

    @property
    def to_update(self):
        return self.status in [Event.States.NOT_STARTED,
                               Event.States.MATCHES_POSTED,
                               Event.States.QUALIFICATION_MATCHES,
                               Event.States.FINAL_MATCHES]

    def set_status_code(self, matches):
        # should we update the elo database with new match data, *or* could
        # there possibly be new matches to post predictions for
        update_ratings_predictions = True

        now = utc.localize(datetime.now())

        if now < (self.event_start-timedelta(1)):
            self.status = Event.States.NOT_STARTED
            update_ratings_predictions = False
        elif now > self.event_end + timedelta(1):
            if self.status == Event.States.FINISHED:
                update_ratings_predictions = False
            else:
                self.status = Event.States.FINISHED
                update_ratings_predictions = True
        elif not matches:
            if now < self.event_end+timedelta(1):
                self.status = Event.States.PRE_MATCHES
            else:
                self.status = Event.States.NO_DATA
            update_ratings_predictions = False
        elif not self.tba_wrapper.has_match_been_played(matches[0]):
            if now < self.event_end+timedelta(1):
                self.status = Event.States.MATCHES_POSTED
                update_ratings_predictions = True
            else:
                self.status = Event.States.NO_DATA
                update_ratings_predictions = False
        else:
            first_unplayed = None
            for match in matches:
                if not self.tba_wrapper.has_match_been_played(match):
                    first_unplayed = match
                    break
            if not first_unplayed and not matches[-1]['comp_level'] == 'qm':
                if not self.status == Event.States.FINISHED:
                    # if event is already finished, no point in updating
                    # predictions as we will already have seen all the matchess
                    update_ratings_predictions = True
                else:
                    update_ratings_predictions = False
                self.status = Event.States.FINISHED
            elif first_unplayed['comp_level'] is 'qm':
                self.status = Event.States.QUALIFICATION_MATCHES
                update_ratings_predictions = True
            else:
                self.status = Event.States.FINAL_MATCHES
                update_ratings_predictions = True

        return update_ratings_predictions
