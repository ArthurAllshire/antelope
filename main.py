from flask import Flask
from flask import render_template
from collections import OrderedDict

app = Flask(__name__)

# the following abomination is just for developing the webpages themselves.
# feel free to turn off your linter
ausc = {'start_year': '2018', 'start_month': 'March', 'start_day': '17',
        'name': 'Southern Cross Regional', 'end_month': 'March',
        'end_day': '18', 'status': 'Quarter Final', "status_code": "qf", "code": "2018ausc",
        'event_stats': [["Team", "Win %"], [4774, 3], [2038, 2], [3838, 1]],
        'upcoming_matches': [
            {'name': "Quals 39", "blue_alliance": ["4774", "3892", "4839"], "blue_win_prob": "37",
             "red_alliance": ["474", "392", "4839"], "red_win_prob": "38"}
        ],
        'finals': {"in_progress": True, "rounds": 3, "final_type": "knockout",
                   "knockout_predictions": [
                       [["4774", "1288", "3829"], 87, 84, 83],
                       [["988", "5", "324"], 1, 2, 5]
                   ]
                   }
        }
events = OrderedDict()

events['2018ausc'] = ausc


@app.route('/')
def index():
    return render_template('index.html', events=events.values())


@app.route('/event/<string:evcode>')
def event(evcode):
    event = events[evcode]
    return render_template('event.html', event=event)


@app.route('/team/<int:team>')
def team(team):
    # TODO: actually make team page
    return str(team)
