from datetime import datetime
from pytz import timezone, utc
from collections import OrderedDict


class Event:
    """Used to represent an individual event. Stores status information,
    and fetches additional information about other events."""

    # numbers are bracket numbers, others are weird bracket types
    PLAYOFF_TYPE_MAPPING = {0: 8, 1: 16, 2: 4, 4: '6-team-round-robin',
                            5: 'DOUBLE_ELIM_8_TEAM', 6: 'BO5_FINALS'}

    class States:
        NOT_STARTED = 0
        PRE_MATCHES = 1
        MATCHES_POSTED = 2
        QUALIFICATION_MATCHES = 3
        FINAL_MATCHES = 4
        FINISHED = 5

    def __init__(self, evcode, tba_wrapper):
        self.tba_wrapper = tba_wrapper
        self.evcode = evcode
        self.get_status()

    def get_status(self):
        # TODO: handle exceptions in the following (ie if no response)
        event_response = self.tba_wrapper.get_raw_event(self.evcode)

        # TODO: add support for different round types
        self.teams_in_bracket = 8

        tz = timezone(event_response['timezone'])

        self.event_start = tz.localize(
                         datetime.strptime(
                             event_response['start_date'], '%Y-%m-%d'))

        self.event_end = tz.localize(
                         datetime.strptime(
                             event_response['end_date'], '%Y-%m-%d'))

        now = utc.localize(datetime.now())

        matches = self.tba_wrapper.get_event_matches(self.evcode)
        # see if ready
        if now < self.event_start:
            self.status = Event.States.NOT_STARTED
        elif not matches:
            self.status = Event.States.PRE_MATCHES
        elif not self.has_match_been_played(matches[0]):
            self.status = Event.States.MATCHES_POSTED
        else:
            first_unplayed = None
            for match in matches:
                if not self.has_match_been_played(match):
                    first_unplayed = match
                    break
            if not first_unplayed:
                self.status = Event.States.FINISHED
            elif first_unplayed['comp_level'] is 'qm':
                self.status = Event.States.QUALIFICATION_MATCHES
            else:
                self.status = Event.States.FINISHED

    def gen_event_dict(self):
        """ Generate a status dict to be returned to be given to the jinja2 templates
        :return: the event dictionary
        """
        # TODO: write this function

    @staticmethod
    def sort_by_match_number(matches):
        """ Sort matches (which is a list of JSON dictionares representing a
        Blue Alliance API event response) by match number """

        comp_levels = OrderedDict()
        comp_levels["qm"] = []
        comp_levels["ef"] = []
        comp_levels["qf"] = []
        comp_levels["sf"] = []
        comp_levels["f"] = []

        for match in matches:
            comp_levels[match["comp_level"]].append(match)
        sorted_matches = []
        for level in comp_levels.values():
            sorted_matches += \
                sorted(level,
                       key=lambda x: (x["match_number"], x["set_number"]))

        return sorted_matches

    @staticmethod
    def has_match_been_played(match):
        """ Determine if match (Match model json) has been played """
        # TODO: check if this method works
        return bool(match['score_breakdown'])
