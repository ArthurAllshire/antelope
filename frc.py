from predict.elo import Elo
from predict.event_predict import EventSimutator


class FRC:

    """Class to tie the rest of the event-getting and predicting stuff together
    to separate it from the flask stuff. """
    def __init__(self, year):
        # load blue alliance key
        with open('tba/key.txt', 'r') as keyfile:
            self.tba_key = keyfile.readline().rstrip('\n')
