import os, requests, json
from datetime import datetime
from utils import ospath, dateutils
path = os.path.dirname(os.path.abspath(__file__))
ospath.checkdirs(path, ["backup", "cache", "data"])

def bulk_cards(t="oracle"):
    now = datetime.now()
    filete = "{}\\cache\\{}-cards-{:04d}{:02d}{:02d}.json".format(path, t, now.year, now.month, now.day)
    try:
        with open(filete, "r", encoding="utf8") as f:                            
            data = json.load(f)
    except:
        bulk_info = requests.get("https://api.scryfall.com/bulk-data/{}-cards".format(t)).json()
        # TODO: utilizar el campo updated_at de bulk_info para determinar si pedir o no
        bulk_data = requests.get(bulk_info["download_uri"])
        with open(filete, "wb") as f:
            f.write(bulk_data.content)
        data = bulk_data.json()
    return data

#getbysetcodecardnum("vma", 321)
def getbysetcodecardnum(setcode, cardnum):
    r = requests.get("https://api.scryfall.com/cards/{}/{}?format=json".format(setcode.lower(), cardnum))
    return r.json()

def query():
    cards = []
    r = requests.get("https://api.scryfall.com/cards/search?q=-t%3Aland&unique=art").json()
    cards.extend(r["data"])
    while r["has_more"]:
        r = requests.get(r["next_page"]).json()
        cards.extend(r["data"])
    return cards