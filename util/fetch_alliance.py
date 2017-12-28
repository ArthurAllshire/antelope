from tba_wrapper import BlueAllianceWrapper
import pickle

tba_key = None
with open('../tba/key.txt', 'r') as keyfile:
    tba_key = keyfile.readline().rstrip('\n')

tba_wrapper = BlueAllianceWrapper(tba_key)

print(tba_wrapper.fetch_alliance_data('2017iri')[1])