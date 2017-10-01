import csv
import requests
import os
import time
import re

basecachedir = "__mycache__"


# base
class Card:
    def __init__(self, id='',name='',edition=''):
        self.id=id
        self.name=name
        self.edition=edition

# detalle
class CardDetails:
    def __init__(self, price=0,count=0,foil=False,language='en',condition='NM'):
        self.price = price
        self.count = count
        self.foil = foil
        self.language = language
        self.condition = condition

# una carta de un inventario (varias entradas de tipo CardDetails)
class InventoryCard(Card):
    def __init__(self, id='',name='',edition=''):
        super().__init__(id, name, edition)
        self.entries = []

# una carta con inventario
class PriceCard(Card):
    def __init__(self, id='',name='',edition='',details=CardDetails()):
        super().__init__(id, name, edition)
        self.price = details.price
        self.count = details.count
        self.foil = details.foil
        self.language = details.language
        self.condition = details.condition

class Deckbox:
    cachedir = "{}/deckbox/{}".format(basecachedir, "{}")

    def inventory():
        cachedir = Deckbox.cachedir.format("inventory")
        req = requests.get("https://deckbox.org/sets/export/125700?format=csv&f=&s=&o=&columns=Image%20URL")

        if not os.path.exists(cachedir):
        	os.makedirs(cachedir)

        filename = "{}/{}.csv".format(cachedir, time.time());
        with open(filename, "w") as f:
            f.write(req.text);

        inventory = []
        reID = "(\d*).jpg$"
        with open(filename) as f:
            reader = csv.DictReader(f, delimiter=",", quotechar='"')
            for row in reader:
                id = re.search(reID, row["Image URL"]).group(1)
                inventorycard = None
                for card in inventory:
                    if (card.id == id):
                        inventorycard = card
                        break
                if (inventorycard is None):
                    inventorycard = InventoryCard(id, row["Name"], row["Edition"])
                    inventory.append(inventorycard)

                inventorycard.entries.append(CardDetails(0,(int)(row["Count"]),True if row["Foil"] == "foil" else False, row["Language"],row["Condition"]))
        count = 0
        for card in inventory:
            for entry in card.entries:
                count = count + entry.count

        print(count)

def test():
    c = InventoryCard('1','asdasd','ed', 22)
    print(c.id)
    print(c.name)
    print(c.edition)
    print(c.count)
