from tba_wrapper import BlueAllianceWrapper
import pickle

tba_key = None
with open('../tba/key.txt', 'r') as keyfile:
    tba_key = keyfile.readline().rstrip('\n')

HEADERS = {'X-TBA-App-Id': 'Arthur Allshire:Antelope',
           'X-TBA-Auth-Key': tba_key}

tba_wrapper = BlueAllianceWrapper(HEADERS)

for year in range(2008, 2018):
    print(year)
    matches = tba_wrapper.get_year_matches(str(year))
    pickle.dump(matches, open('../cache/'+str(year)+'matches.p', 'wb'))
