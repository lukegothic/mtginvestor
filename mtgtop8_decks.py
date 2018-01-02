import threading
from queue import Queue
import time
import datetime
from lxml import html
import requests
import re
import os
import codecs
import copy
import math

theformat = "PAU"
meses = 2
cachedir = "cache/mtgtop8/decks"

if not os.path.exists(cachedir):
	os.makedirs(cachedir)

dpp = 25
rDeck = "event\?e=(\d*)&d=(\d*)&f=" + theformat
lock = threading.Lock()

def getDeckIds(p):
	pd = {
		"current_page": p,
		"format": theformat,
		"date_start": thedate,
		"compet_check[P]": 1,
		"compet_check[M]": 1,
		"compet_check[C]": 1,
		"compet_check[R]": 1
	}
	page = requests.post("http://mtgtop8.com/search", pd)
	tree = html.fromstring(page.text)
	if p == 1:
		a = tree.xpath("//div[@class='w_title']")[0].text_content().replace(" decks matching", "")
		paget = math.ceil((int)(a) / dpp)
		for pagen in range(2, paget + 1):
			q.put(pagen)
	rows = tree.xpath("//tr[@class='hover_tr']/td[@class='S11']/a")
	for row in rows:
		deckids.append(re.search(rDeck, row.attrib["href"]).group(2))
def getDeck(deckid):
	deckfile = "{}/{}.txt".format(cachedir, deckid)
	try:
		with codecs.open(deckfile, "r", "utf-8") as f:
			data = f.read()
	except IOError:
		page = requests.get("http://mtgtop8.com/mtgo?d={}".format(deckid))
		with codecs.open(deckfile, "w", "utf-8") as f:
			data = page.text
			f.write(data)
	deck = []
	lines = data.split("\r\n")
	issb = False
	for line in lines:
		if line != "":
			if line == "Sideboard":
				issb = True
			else:
				card = line.replace(" ", "#", 1).split("#")
				deck.append({
					"name": card[1],
					"quantity": (int)(card[0]),
					"issb": issb
				})
	decks.append(deck)
def searchworker():
	while True:
		getDeckIds(q.get())
		q.task_done()
def deckworker():
	while True:
		getDeck(q.get())
		q.task_done()
deckids = []
decks = []
q = Queue()
def doSearch():
	# Obtener IDs de las deck que corresponden con la query que se ha hecho
	# No se cachea para tener siempre la ultima version de la peticion
	if True:
		for i in range(4):
			t = threading.Thread(target=searchworker)
			t.daemon = True
			t.start()
		q.put(1)
		q.join()
	else:
		files = os.listdir(cachedir)
		for f in files:
			deckids.append((int)(f.replace(".txt", "")))
	# TODO: MANEJAR SI EL SERVIDOR SE ENCUENTRA EN MANTENIMIENTO
	# Obtener las Decks que corresponden con los ID encontrados
	# Se cachean porque no cambian
	# Aqui tambien se realiza la conversion de decklists a objetos deck
	# Dado que se realizan aperturas de ficheros
	for i in range(4):
		t = threading.Thread(target=deckworker)
		t.daemon = True
		t.start()
	for deckid in deckids:
		q.put(deckid)
	q.join()

#start = time.perf_counter()
archetypes = [{
	"name": "Burn",
	"cards": ["Lava Spike"]
},{
	"name": "Tron",
	"cards": ["Urza's Tower"]
}, {
	"name": "Elves",
	"cards": ["Elvish Vanguard"]
}, {
	"name": "Stompy",
	"cards": ["Young Wolf", "Skarrgan Pit-Skulk"]
}, {
	"name": "Delver",
	"cards": ["Delver of Secrets"]
}, {
	"name": "Inside Out Combo",
	"cards": ["Tireless Tribe", "Inside Out"]
}, {
	"name": "Tortured Existence",
	"cards": ["Tortured Existence"]
}, {
	"name": "Bogles",
	"cards": ["Slippery Bogle", "Gladecover Scout"]
}, {
	"name": "Affinity",
	"cards": ["Frogmite", "Myr Enforcer"]
}, {
	"name": "Flicker Combo",
	"cards": ["God-Pharaoh's Faithful"]
}, {
	"name": "Reanimator",
	"cards": ["Exhume"]
}, {
	"name": "Boros",
	"cards": ["Glint Hawk"]
}, {
	"name": "Slivers",
	"cards": ["Muscle Sliver"]
}, {
	"name": "Blitz Combo",
	"cards": ["Kiln Fiend"]
}, {
	"name": "MBC",
	"cards": ["Chittering Rats", "Sign in Blood"]
}, {
	"name": "Orzhov Control",
	"cards": ["Pestilence", "Guardian of the Guildpact"]
}, {
	"name": "MWA",
	"cards": ["Squadron Hawk"]
}, {
	"name": "Goblins",
	"cards": ["Goblin Bushwhacker"]
}, {
	"name": "UB Control",
	"cards": ["Chainer's Edict", "Counterspell", "Echoing Decay"]
}]

theformat = "PAU"
cuantosmeses = 2
thedate = (datetime.date.today() - datetime.timedelta(cuantosmeses * 365/12)).strftime("%d/%m/%Y")
doSearch()
print("Se han encontrado {} decks desde {}".format(len(decks), thedate))
for arch in archetypes:
	arch["decks"] = []
	print(arch["name"])
	for deck in decks:
		archcardindeck = 0
		for archcard in arch["cards"]:
			for card in deck:
				if not card["issb"] and card["name"] == archcard:
					archcardindeck += 1
					break
		if archcardindeck == len(arch["cards"]):
			arch["decks"].append(deck)
	print(len(arch["decks"]))

#print('time:',time.perf_counter() - start)

#select chr(34)||trim(name)||chr(34)||':'||(quantity/2.0)||',' from mtgtop8_staples order by quantity desc
