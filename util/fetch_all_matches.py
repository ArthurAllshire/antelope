from tba_wrapper import BlueAllianceWrapper
import pickle

tba_key = None
with open('../tba/key.txt', 'r') as keyfile:
    tba_key = keyfile.readline().rstrip('\n')

tba_wrapper = BlueAllianceWrapper(tba_key)

for year in range(2008, 2018):
    print(year)
    matches = tba_wrapper.get_year_matches(str(year))
    pickle.dump(matches, open('../cache/'+str(year)+'matches.p', 'wb'))
