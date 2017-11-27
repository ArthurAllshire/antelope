from elo import FRCElo

elo = FRCElo(20, 1350, 20)

for i in range(6):
    elo.init_team(str(i))

print(elo.elo)

blue = ["0", "1", "2"]
red = ["3", "4", "5"]

elo.update(blue, 100, red, 0)

print(elo.elo)

print(elo.predict(blue, red))
elo.update(blue, 0, red, 100)
print(elo.elo)
