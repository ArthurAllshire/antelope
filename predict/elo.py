import statistics
from collections import deque
from scipy.stats import norm
from collections import namedtuple

Match = namedtuple('Match', ['blue_teams', 'red_teams', 'blue_score', 'red_score',
                             'comp_level'])

class FRCElo(object):
    STDEV_LEN = 500

    def __init__(self, qm_K, fm_K, new_team_rating, init_stdev):
        """
        :param K: Elo K-factor. Used to determine how responsive the algorithm
        is to match results.
        :param new_team_rating: The Elo rating that new teams are initialised
        with.
        :param init_stdev: The initial standard deviation factor used to
        normalise the score difference.
        """
        # Elo K-factor
        self.qm_K = qm_K
        self.fm_K = fm_K
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

    def predict(self, raw_match=None, teams=None):
        if not alliance_scores:
            match = FRCElo.get_match_data(raw_match)
        else:
            # option to just pass in teams, not match
            match = Match(blue_teams=teams['blue'], red_teams=teams['red'])

        try:
            blue_elo = sum([self.elo[team] for team in match.blue_teams])
            red_elo = sum([self.elo[team] for team in match.red_teams])
        except KeyError:
            for team in match.blue_teams + match.red_teams:
                if team not in self.elo.keys():
                    self.init_team(team)

            blue_elo = sum([self.elo[team] for team in match.blue_teams])
            red_elo = sum([self.elo[team] for team in match.red_teams])

        elo_diff = float(blue_elo - red_elo)

        blue_win_prob = self.diff_to_prob(elo_diff)

        return blue_win_prob

    def diff_to_prob(self, diff):
        return norm.cdf(x=diff/550, loc=0, scale=1)

    def predict_margin(self, raw_match):
        # what was the prior probability of the blue alliance winning the match?
        blue_win_prior = self.predict(raw_match)
        # based on our prior probability of blue victory, calculate their
        # expected margin of victory
        expected_blue_margin = norm.ppf(blue_win_prior, loc=0, scale=self.stdev)
        return expected_blue_margin


    def recalculate_stdev(self, blue_score, red_score):
        self.stdev_i += 1
        self.stdev_scores.append(blue_score)
        self.stdev_scores.append(red_score)
        if self.stdev_i % 20 == 0:
            self.stdev = statistics.stdev(self.stdev_scores)

    def update(self, raw_match):
        """Apply the Elo update after a match.
        :param blue_alliance: List of team numbers (as string).
        :param blue_score: Score achieved by blue alliance.
        :param red_alliance: List of team numbers (as string).
        :param red_score:  Score achieved by red alliance.
        :param K: Elo K-factor. Used to determine how responsive the algorithm
        is to match results. Defaults to K factor provided in constructor.
        """
        match = FRCElo.get_match_data(raw_match)

        try:
            blue_elo = sum([self.elo[team] for team in match.blue_teams])
            red_elo = sum([self.elo[team] for team in match.red_teams])
        except KeyError:
            for team in match.blue_teams + match.red_teams:
                if team not in self.elo.keys():
                    self.init_team(team)

            blue_elo = sum([self.elo[team] for team in match.blue_teams])
            red_elo = sum([self.elo[team] for team in match.red_teams])

        self.recalculate_stdev(match.blue_score, match.red_score)

        expected_blue_margin = self.predict_margin(raw_match)

        blue_margin = float(match.blue_score - match.red_score)
        margin_error = (blue_margin - expected_blue_margin)
        K = self.qm_K if match.comp_level == 'qm' else self.fm_K
        update = K * margin_error / self.stdev

        for team in match.blue_teams:
            self.elo[team] += update
        for team in match.red_teams:
            self.elo[team] -= update

    def init_team(self, team_number, rating=None):
        """Add a new team with rating rating.
        :param team_number: The team number which the team will start with.
        :param rating: The Elo rating the team will start with. Defaluts to one
        provided in constructor.
        """
        self.elo[str(team_number)] = rating if rating else self.new_team_rating

    def next_year(self, reversion_score, reversion_factor, new_stdev):
        for team, elo in self.elo.items():
            self.elo[team] = (self.elo[team] -
                              reversion_factor * (self.elo[team] - reversion_score))
        self.stdev = new_stdev
        self.stdev_scores = deque([], maxlen=FRCElo.STDEV_LEN)
        self.stdev_i = 0

    @staticmethod
    def get_match_data(match):
        blue_teams = match["alliances"]["blue"]["team_keys"]
        red_teams = match["alliances"]["red"]["team_keys"]
        blue_score = match["alliances"]["blue"]["score"]
        red_score = match["alliances"]["red"]["score"]
        comp_level = match["comp_level"]
        return Match(blue_teams, red_teams, blue_score, red_score, comp_level)
