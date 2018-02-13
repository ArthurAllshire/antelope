from predict.elo import FRCElo
from util.tba_wrapper import BlueAllianceWrapper
from util.event import Event
from collections import OrderedDict
import threading
import time


class FRC(threading.Thread):

    """Class to tie the rest of the event-getting and predicting stuff together
    to separate it from the flask stuff. """
    def __init__(self, current_year, thread_name):
        self.current_year = current_year
        self.current_year_str = str(current_year)
        super().__init__(name=thread_name)

    def setup(self):

        # load blue alliance key
        with open('tba/key.txt', 'r') as keyfile:
            self.tba_key = keyfile.readline().rstrip('\n')

        self.tba_wrapper = BlueAllianceWrapper(self.tba_key)

        self.elo = FRCElo(qm_K=20, fm_K=5, new_team_rating=1350, init_stdev=50)
        self.process_previous_years()

        ev_dicts = self.tba_wrapper.get_year_events(self.current_year)
        self.events = OrderedDict()
        for ev_dict in ev_dicts:
            event_code = self.current_year_str+ev_dict['event_code']
            self.events[event_code] = Event(event_code, self.elo, self.tba_wrapper)

    def process_previous_years(self):
        for year in range(2008, self.current_year):
            print("Getting year matches %s" % year)
            year_events = self.tba_wrapper.get_year_matches(str(year))
            print("Got year matches %s" % year)

            print("Running ELO for year %s" % year)
            # year events is an OrderedDict in chronological order, with event
            # codes as keys
            self.process_year_matches(year_events)
            self.elo.next_year(1500, 0.2, 50)

    def process_year_matches(self, year_events):
        for event_code, event in year_events.items():
            for match in event:
                self.elo.update(match)

    def run(self):
        while True:
            start = time.monotonic()
            for event in self.events.values():
                if event.to_update:
                    event.update_event_status()
            to_wait = 180-(time.monotonic()-start)
            if to_wait > 0:
                print("%s sleeping for %s seconds" % (self.name, to_wait))
                time.sleep(to_wait)
