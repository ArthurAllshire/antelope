class EventPredictor:
    def __init__(self, elo, event):
        self.elo = elo
        self.event = event

    def get_upcoming_predictions(self):
        # TODO