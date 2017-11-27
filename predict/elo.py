import statistics
from collections import deque


class FRCElo(object):
    STDEV_LEN = 400

    def __init__(self, K, new_team_rating, init_stdev):
        """
        :param K: Elo K-factor. Used to determine how responsive the algorithm
        is to match results.
        :param new_team_rating: The Elo rating that new teams are initialised
        with.
        :param init_stdev: The initial standard deviation factor used to
        normalise the score difference.
        """
        # Elo K-factor
        self.K = K
        # Ratings that new teams are initialised with
        self.new_team_rating = new_team_rating
        # Dict where key, value is "team_no", elo_rating
        self.elo = {}
        # Standard deviation of results used to normalise diff
        self.stdev = init_stdev
        # deque used to calculate standard deviations for match scores
        self.stdev_scores = deque([], maxlen=FRCElo.STDEV_LEN)
        # used so we only calculate stdev every so often not every update
        # helps reduce CPU load
        self.stdev_i = 0

    def predict(self, blue_alliance, red_alliance):
        """ alliances are to be lists of strings corresponding
        to team number """
        try:
            blue_elo = sum([self.elo[team] for team in blue_alliance])
            red_elo = sum([self.elo[team] for team in red_alliance])
        except KeyError:
            for team in blue_alliance + red_alliance:
                if team not in self.elo.keys():
                    self.init_team(team)

            blue_elo = sum([self.elo[team] for team in blue_alliance])
            red_elo = sum([self.elo[team] for team in red_alliance])

        elo_diff = red_elo - blue_elo
        print(elo_diff)

        blue_win_prob = self.diff_to_prob(elo_diff)

        return blue_win_prob

    def diff_to_prob(self, diff):
        return 1. / (1. + 10. ** (diff / 400.))

    def recalculate_stdev(self, blue_score, red_score):
        self.stdev_i += 1
        self.stdev_scores.append(blue_score)
        self.stdev_scores.append(red_score)
        if self.stdev_i % 100 == 0 and len(self.stdev_scores) < 800:
            self.stdev = statistics.stdev(self.stdev_scores)

    def update(self, blue_alliance, blue_score,
               red_alliance, red_score, K=None):
        """Apply the Elo update after a match.
        :param blue_alliance: List of team numbers (as string).
        :param blue_score: Score achieved by blue alliance.
        :param red_alliance: List of team numbers (as string).
        :param red_score:  Score achieved by red alliance.
        :param K: Elo K-factor. Used to determine how responsive the algorithm
        is to match results. Defaults to K factor provided in constructor.
        """
        K = K if K else self.K
        try:
            blue_elo = sum([self.elo[team] for team in blue_alliance])
            red_elo = sum([self.elo[team] for team in red_alliance])
        except KeyError:
            for team in blue_alliance + red_alliance:
                if team not in self.elo.keys():
                    self.init_team(team)
            blue_elo = sum([self.elo[team] for team in blue_alliance])
            red_elo = sum([self.elo[team] for team in red_alliance])

        self.recalculate_stdev(blue_score, red_score)

        # predicted_score_diff = (blue_elo - red_elo) * 0.004
        score_diff = (blue_score - red_score) / self.stdev
        predicted_score_diff = (blue_elo - red_elo) * 0.004 * self.stdev
        update = K * (score_diff - predicted_score_diff)
        print("update %s" % update)
        print("stdov %s" % self.stdev)
        print("score diff %s" % score_diff)
        print("predicted %s" % predicted_score_diff)

        try:
            for team in blue_alliance:
                self.elo[team] += update
            for team in red_alliance:
                self.elo[team] -= update
        except KeyError:
            # team must not exist yet - make a new one
            for team in blue_alliance + red_alliance:
                if team not in self.elo.keys():
                    self.init_team(team)
            for team in blue_alliance:
                self.elo[team] += update
            for team in red_alliance:
                self.elo[team] -= update
                # and yes, i am aware it is not beautiful or pythonic or whatever
                # but i dont want to have to iterate over the array every single
                # time i update the elo. there may be a more efficient way to do
                # it but i dont really care

    def init_team(self, team_number, rating=None):
        """Add a new team with rating rating.
        :param team_number: The team number which the team will start with.
        :param rating: The Elo rating the team will start with. Defaluts to one
        provided in constructor.
        """
        self.elo[str(team_number)] = rating if rating else self.new_team_rating

    def next_year(self, reversion_score, reversion_factor, new_stdev):
        for team, elo in sorted(self.elo.items()):
            self.elo[team] = (self.elo[team] -
                              reversion_factor * (self.elo[team] - reversion_score))
        self.stdev = new_stdev
        self.stdev_scores = deque([], maxlen=FRCElo.STDEV_LEN)
        self.stdev_i = 0
