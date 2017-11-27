"""Testing out and experimenting with the prediction algorithm"""

from elo import FRCElo
import pickle
import statistics
import math

default_stdev = 20

qm_elo = FRCElo(20, 1350, default_stdev)
fm_elo = FRCElo(20, 1350, default_stdev)

# used to calculate standard deviation
SCORE_QUEUE_FINAL_LEN = 800

briers = []
year_briers = []

predictions_outcomes = []


for year in range(2008, 2018):
    with open("../cache/" + str(year) + "matches.p", "rb") as year_file:
        year_events = pickle.load(year_file)
        processed_teams = []
        for event in year_events.values():
            for match in event:
                # print(match)
                blue = match["alliances"]["blue"]["team_keys"]
                red = match["alliances"]["red"]["team_keys"]

                if match["comp_level"] == "qm":
                    forecast = qm_elo.predict(blue, red)
                else:
                    forecast = fm_elo.predict(blue, red)
                # forecast = (qm_elo.predict(blue, red)
                #         if match["comp_level"] == "qm"
                #         else fm_elo.predict(blue, red))

                blue_score = match["alliances"]["blue"]["score"]
                red_score = match["alliances"]["red"]["score"]

                margin = blue_score - red_score
                outcome = 0.5 if margin == 0 else (1 if margin > 0 else 0)
                briers.append((forecast - outcome)**2)

                if year == 2017:
                    predictions_outcomes.append((forecast, outcome))

                qm_K = 15 if match["comp_level"] == "qm" else 2
                fm_K = 15 if match["comp_level"] == "qm" else 5

                qm_elo.update(blue, blue_score, red, red_score, K=qm_K)
                fm_elo.update(blue, blue_score, red, red_score, K=fm_K)

        print("%s year brier %s" % (year, statistics.mean(briers)))
        year_briers.append(statistics.mean(briers))
        briers = []
        qm_elo.next_year(1450, 0.2, default_stdev)
        fm_elo.next_year(1450, 0.2, default_stdev)

print(statistics.mean(year_briers))

predict_buckets = [0 for i in range(20)]
outcome_buckets = [0 for i in range(20)]

for match in predictions_outcomes:
    bucket_num = math.floor(match[0] * 20)
    if not (match[1] == 0.5):
        predict_buckets[bucket_num] += 1
        outcome_buckets[bucket_num] += match[1]

calibration_score = 0
for i, num_predictions, num_outcomes in zip(
        range(0, 20), predict_buckets, outcome_buckets):
    bucket_mean = ((i * 5) + 2.5) / 100
    print("%s - %s" % (bucket_mean, num_outcomes / num_predictions))
    calibration_score += abs(bucket_mean - (num_outcomes / num_predictions))

print(calibration_score)
