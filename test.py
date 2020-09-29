import json, glob, os
from endpoints import scryfall

filete = "querycontest.json"
if not os.path.exists(filete):
    cards = scryfall.query()
    with open(filete, "w") as f:
        json.dump(cards, f)
else:
    with open(filete) as f:
        cards = json.load(f)

cardids = [c["id"] for c in cards]
for imagePath in glob.glob("Y:\\code\\mtginvestor\\output\\crops\\*.jpg"):
    if not imagePath.replace(".jpg", "").replace("Y:\\code\\mtginvestor\\output\\crops\\", "") in cardids:
        os.remove(imagePath)