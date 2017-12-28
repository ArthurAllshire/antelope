from flask import Flask, request
from flask import render_template
from frc import FRC

app = Flask(__name__)

# the following abomination is just for developing the webpages themselves.
# feel free to turn off your linter
ausc = {'start_year': '2018', 'start_date': 'March 17',
        'name': 'Southern Cross Regional', 'end_date': 'March 18',
        'status': 'Quarter Finals', "status_code": "qf", "code": "2018ausc",
        'event_stats': [["Team", "Win %"], [4774, 3], [2038, 2], [3838, 1]],
        'upcoming_matches': [
            {'name': "Quals 39", "blue_alliance": ["4774", "3892", "4839"], "blue_win_prob": "63",
             "red_alliance": ["474", "392", "4839"], "red_win_prob": "37"},
            {'name': "Quals 40", "blue_alliance": ["893", "4853", "4473"], "blue_win_prob": "15",
             "red_alliance": ["3839", "7171", "1112"], "red_win_prob": "85"}
            ], 'previous_matches': [
            {'name': "Quals 38", "blue_alliance": ["4774", "3892", "4839"], "blue_win_prob": "63",
             "red_alliance": ["474", "392", "4839"], "red_win_prob": "37"},
            {'name': "Quals 37", "blue_alliance": ["893", "4853", "4473"], "blue_win_prob": "15",
             "red_alliance": ["3839", "7171", "1112"], "red_win_prob": "85"}
                ],
        'finals': {"in_progress": True, "rounds": 3, "final_type": "knockout",
                   "knockout_predictions": [
                       [["4774", "1288", "3829"], 87, 53, 35],
                       [["6188", "5421", "5174"], 75, 51, 25],
                       [["4321", "1895", "6242"], 63, 32, 17],
                       [["3132", "284", "4921"], 43, 21, 20]
                   ]
                   }
        }

hiho = {'start_year': '2018', 'start_date': 'April 5',
        'name': 'Hawaii Regional', 'end_date': 'April 7',
        'status': 'Qualifications', "status_code": "qm", "code": "2018hiho",
        'event_stats': [["Alliance", "Win %"], [3829, 83], [2038, 2], [3838, 1]],
        'upcoming_matches': [
            {'name': "Quals 39", "blue_alliance": ["4774", "3892", "4839"], "blue_win_prob": "37",
             "red_alliance": ["474", "392", "4839"], "red_win_prob": "38"}
        ], 'previous_matches': [
            {'name': "Quals 38", "blue_alliance": ["4774", "3892", "4839"], "blue_win_prob": "63",
             "red_alliance": ["474", "392", "4839"], "red_win_prob": "37"},
            {'name': "Quals 37", "blue_alliance": ["893", "4853", "4473"], "blue_win_prob": "15",
             "red_alliance": ["3839", "7171", "1112"], "red_win_prob": "85"}
                ],
        'finals': {"in_progress": False, "rounds": 3, "final_type": "knockout",
                   "knockout_predictions": [
                       [["4774", "1288", "3829"], 87, 84, 83],
                       [["988", "5", "324"], 1, 2, 5]
                   ]
                   }
        }

# events = OrderedDict()

# events['2018ausc'] = ausc
# events['2018hiho'] = hiho
frc = FRC(2017, 'backend-thread')
frc.setup()
frc.start()


@app.route('/')
def index():
    events = []
    past_events = []
    for event in frc.events.values():
        if event.event_dict['upcoming_matches']:
            events.append(event.event_dict)
        else:
            past_events.append(event.event_dict)
    return render_template('index.html', events=events, past_events=past_events)


@app.route('/event/<string:event_code>')
def event(event_code):
    event = frc.events[event_code].event_dict
    return render_template('event.html', event=event)


@app.route('/team/<int:team>')
def team(team):
    # TODO: actually make team page
    return str(team)


@app.route('/tba-webhook', methods=['POST'])
def tba_webhook():
    msg_data = request.json['message_data']
    msg_type = request.json['message_type']
    if msg_type == 'verification':
        print('TBA verification key: %s' % msg_data)
