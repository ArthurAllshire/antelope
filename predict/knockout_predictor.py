from collections import OrderedDict
import random
from typing import List
from copy import copy


class Alliance:
    def __init__(self, teams: List[str], alliance_num: int,
                 current_round, current_round_record, levels):
        self.teams = teams
        self.alliance_num = alliance_num
        self.passed_round = OrderedDict([(level, 0) for level in levels])
        self.current_round = current_round
        self.current_round_record = current_round_record
        for round in self.passed_round.keys():
            self.passed_round[round] = True
            if round == current_round:
                break

    def through_percent(self, num_sims):
        through_percentages = copy(self.passed_round)
        for level, passed_number in through_percentages.items():
            through_percentages[level] = passed_number/num_sims
        return through_percentages


class KnockoutPredictor:

    EIGHT_TEAM_BRACKET = (((1, 8), (4, 5)), ((2, 7), (3, 6)))

    levels = ['ef', 'qf', 'sf', 'fm', 'won']

    def __init__(self, event, knockout_type, elo, tba_wrapper, is_sim=False):
        self.event = event
        self.knockout_type = knockout_type
        self.elo = elo
        self.tba_wrapper = tba_wrapper
        self.is_sim = is_sim

    def simulate_bracket_knockout(self):
        alliance_data = self.tba_wrapper.fetch_alliance_data(self.event.event_code)
        levels = self.levels[1:-1]
        alliances = self.generate_initial_state(alliance_data, levels)

        starting_round = 'qf'

        num_sims = 1000

        for i in range(num_sims):
            bracket = self.generate_starting_bracket(alliances, starting_round)
            for level in levels:
                # store all the alliances through this level in a dict by number
                self._alliances_through = {}
                self.recursive_bracket_simulate(bracket, len(self.levels)-2)

                # add one to the count of each alliance getting through this level
                for alliance in self._alliances_through.values():
                    alliance.passed_round[level] += 1

        simulation_results = []
        for alliance in alliances:
            through_percentages = alliance.through_percent(num_sims)
            simulation_results.append([alliance.teams, through_percentages])

        # sort by the chance of winning the comp
        simulation_results = sorted(simulation_results,
                                    key=lambda x: x[1]['fm'])

        return simulation_results

    def recursive_bracket_simulate(self, bracket, level_number):
        if all([isinstance(n, Alliance) for n in bracket]):
            if any(self.levels.index(alliance.current_round) > level_number
                    for alliance in bracket):
                if self.levels.index(bracket[0].current_round) > level_number:
                    winner = bracket[0]
                else:
                    winner = bracket[1]
            else:
                record = [bracket[0].current_round_record['wins'],
                          bracket[1].current_round_record['losses']]
                winner = self.simulate_match(bracket, record)
            self._alliances_through[winner.alliance_num] = winner
            return winner
        else:
            for i, half_bracket in enumerate(bracket):
                bracket[i] = self.recursive_bracket_simulate(
                        half_bracket, level_number-1)
            return bracket

    def simulate_match(self, matchup, record, to_win=2):
        while record[0] < to_win and record[1] < to_win:
            a_win_prob = self.elo.predict(teams={'blue': matchup[0].teams, 'red': matchup[1].teams})
            if random.uniform(0, 1) <= a_win_prob:
                record[0] += 1
            else:
                record[1] += 1
        if record[0] > record[1]:
            return matchup[0]
        else:
            return matchup[1]

    def generate_initial_state(self, alliance_data, levels):
        alliances = []
        for num, raw_alliance in enumerate(alliance_data, start=1):
            # TODO: Add support for 3rd pick
            teams = raw_alliance['picks'][:3]
            if raw_alliance['backup'] and raw_alliance['out'] in teams \
                    and not self.is_sim:
                teams[teams.index(raw_alliance['out'])] = raw_alliance['in']
            try:
                # parse alliance number if available
                alliance_num = int(raw_alliance['name'].lstrip('Alliance '))
            except KeyError:
                # else just assume the alliances are in order
                alliance_num = num

            if not self.is_sim:
                level = raw_alliance['level']
                record = raw_alliance['status']['current_level_record']
            else:
                level = 'qf'
                record = {'wins': 0, 'losses': 0}
            alliance = Alliance(teams, alliance_num, level, record, levels)

            alliances.append(alliance)

        return alliances

    def generate_starting_bracket(self, alliances, bracket_min_level):
        if bracket_min_level == "qf":
            bracket = [[[alliances[0], alliances[7]], [alliances[3], alliances[4]]],
                       [[alliances[1], alliances[6]], [alliances[2], alliances[5]]]]
            return bracket
        else:
            print("Error: invalid bracket type")
            raise Exception
