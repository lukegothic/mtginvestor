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
import csv
import sqlite3
import mkm
import hashlib

basedir = "__mycache__/mtgtop8"
deckdir = "{}/decks".format(basedir)
searchdir = "{}/search".format(basedir)
if not os.path.exists(deckdir):
	os.makedirs(deckdir)
if not os.path.exists(searchdir):
	os.makedirs(searchdir)
dpp = 25
rDeck = "event\?e=(\d*)&d=(\d*)&f="
lock = threading.Lock()

# ARCHETYPES
archetypes = [ {
	"name": "Inside Out Combo",
	"cards": ["Tireless Tribe", "Inside Out"]
}, {
	"name": "Flicker Combo",
	"cards": ["God-Pharaoh's Faithful"]
}, {
	"name": "Blitz Combo",
	"cards": ["Kiln Fiend", "Nivix Cyclops"]
}, {
	"name": "Affinity",
	"cards": ["Frogmite", "Myr Enforcer"]
},{
	"name": "Tron",
	"cards": ["Urza's Tower"]
}, {
	"name": "Elves",
	"cards": ["Birchlore Rangers"]
}, {
	"name": "Stompy",
	"cards": ["Young Wolf", "Skarrgan Pit-Skulk"]
}, {
	"name": "Bogles",
	"cards": ["Slippery Bogle"]
}, {
	"name": "Slivers",
	"cards": ["Muscle Sliver"]
},{
	"name": "Tortured Existence",
	"cards": ["Tortured Existence"]
},{
	"name": "Burn",
	"cards": ["Lava Spike", "Chain Lightning"]
}, {
	"name": "Delver",
	"cards": ["Delver of Secrets"]
}, {
	"name": "Ninja Aggro", # solape con delver
	"cards": ["Faerie Miscreant", "Ninja of the Deep Hours", "Spellstutter Sprite"]
}, {
	"name": "Reanimator", # solape con UB control
	"cards": ["Exhume"]
}, {
	"name": "UB Control",
	"cards": ["Chainer's Edict", "Counterspell"]
}, {
	"name": "Boros",
	"cards": ["Glint Hawk"]
}, {
	"name": "RW Tokens", # solape con Boros
	"cards": ["Battle Screech", "Dragon Fodder"]
}, {
	"name": "MBC",
	"cards": ["Chittering Rats", "Phyrexian Rager"]
}, {
	"name": "Orzhov Control",
	"cards": ["Pestilence", "Guardian of the Guildpact"]
}, {
	"name": "MonoW",
	"cards": ["Squadron Hawk"]
}, {
	"name": "Goblins",
	"cards": ["Goblin Bushwhacker"]
}]
# FORMATO
theformat = "PAU"
# MESES DE DATOS
meses = 3
thedate = (datetime.date.today() - datetime.timedelta(meses * 365/12)).strftime("%d/%m/%Y")
decks = []
staples = {}
def getDeckIds(p):
	uniqueid = hashlib.sha1("{}{}{}".format(theformat,thedate,p).encode()).hexdigest()
	filete = "{}/{}.html".format(searchdir,uniqueid)
	try:
		with open(filete) as f:
			data = f.read()
	except:
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
		data = page.text
		with open(filete, "w") as f:
			f.write(data)

	tree = html.fromstring(data)
	if p == 1:
		a = tree.xpath("//div[@class='w_title']")[0].text_content().replace(" decks matching", "")
		paget = math.ceil((int)(a) / dpp)
		for pagen in range(2, paget + 1):
			q.put(pagen)
	rows = tree.xpath("//tr[@class='hover_tr']/td[@class='S11']/a")
	for row in rows:
		deckids.append(re.search(rDeck, row.attrib["href"]).group(2))
def getDeck(deckid):
	deckfile = "{}/{}.txt".format(deckdir, deckid)
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
		files = os.listdir(deckdir)
		for f in files:
			deckids.append((int)(f.replace(".txt", "")))
	# TODO: MANEJAR SI EL SERVIDOR SE ENCUENTRA EN MANTENIMIENTO
	# Obtener las Decks que corresponden con los ID encontrados
	# Se cachean porque no cambian
	# Aqui tambien se realiza la conversion de decklists a objetos deck
	# Dado que se realizan aperturas de ficheros
	deckids.sort()
	for i in range(4):
		t = threading.Thread(target=deckworker)
		t.daemon = True
		t.start()
	for deckid in deckids:
		q.put(deckid)
	q.join()
	print("Se han encontrado {} decks desde {}".format(len(decks), thedate))
def getMinEuroPrice(cards):
	cardnames = []
	for card in cards:
	    cardnames.append("c.name = '{0}' OR c.name LIKE '{0} //%'".format(card.replace("'", "''")))
	cardnames = " OR ".join(cardnames)
	dbconn = sqlite3.connect("__offlinecache__/scryfall/scryfall.db")
	dbconn.row_factory = sqlite3.Row
	c = dbconn.cursor()
	sql = "select c.name, c.setcode, c.idmkm from sets s left join cards c on s.code = c.setcode WHERE ({}) AND set_type IN ('expansion', 'core') ORDER BY released_at".format(cardnames)
	# with open("sql.txt", "w") as f:
	# 	f.write(sql)
	dbcards = c.execute(sql).fetchall()
	# with open("proxy.txt", "w") as f:
	# 	lasted = None
	# 	for dbcard in dbcards:
	# 		if lasted != dbcard["setcode"]:
	# 			lasted = dbcard["setcode"]
	# 			for i in range(2):
	# 				f.write("Mountain\n")
	# 		if not dbcard["name"] in ["Plains", "Island", "Swamp", "Mountain", "Forest"]:
	# 			f.write(dbcard["name"] + "\n")
	priceobj = {}
	for card in cards:
		if card in ["Plains", "Island", "Swamp", "Mountain", "Forest"]:
			priceobj[card] = 0.01
		else:
			minprice = 10000
			matches = []
			for dbcard in dbcards:
				if (dbcard["name"].startswith(card)):
					matches.append(dbcard)
			print("{} ({} versiones)".format(card, len(matches)))
			for m in matches:
				if not m["idmkm"] is None:
					qcard = {
						"idmkm": m["idmkm"],
						"isFoil": False,
						"idLanguage": "EN"
					}
					mkm.getPriceDataSingle(qcard)
					if qcard["mkmprice"] < minprice:
						minprice = qcard["mkmprice"]
			priceobj[card] = minprice
			print("Min: {}".format(priceobj[card]))
	return priceobj
def clasificarDecksPorArquetipos():
	for arch in archetypes:
		arch["decks"] = []
		for i, deck in reversed(list(enumerate(decks))):
			archcardindeck = 0
			for archcard in arch["cards"]:
				for card in deck:
					if not card["issb"] and card["name"] == archcard:
						archcardindeck += 1
						break
			if archcardindeck == len(arch["cards"]):
				arch["decks"].append(deck)
				decks.pop(i)
	if len(decks) > 0:
		print("Hay {} sin arquetipo".format(len(decks)))
		input()
		for i, deck in enumerate(decks):
			print("SIN ARQ {}".format(i+1))
			for card in deck:
				print("{}{} {}".format("SB: " if card["issb"] else "", card["quantity"], card["name"]))
			print()
def obtenerStaples():
	for arch in archetypes:
		#fields.append(arch["name"])
		for deck in arch["decks"]:
			added = []
			for card in deck:
				if not card["name"] in staples:
					staples[card["name"]] = {}
				if not arch["name"] in staples[card["name"]]:
					staples[card["name"]][arch["name"]] = 1
					added.append(card["name"])
				else:
					if not card["issb"] or (card["issb"] and not card["name"] in added):
						staples[card["name"]][arch["name"]] += 1
						added.append(card["name"])
	print("{} different cards".format(len(staples)))
def escribirCSV():
	#obtener todos los datos necesarios de la db
	dbconn = sqlite3.connect("__offlinecache__/scryfall/scryfall.db")
	dbconn.row_factory = sqlite3.Row
	c = dbconn.cursor()
	sql = "select distinct name, color, type, min(usd) as usd, min(eur) as eur from cards WHERE name in ('{}') GROUP BY name, color, type".format("','".join(c.replace("'", "''") for c in staples))
	dbcards = c.execute(sql).fetchall()
	print("{} DB cards".format(len(dbcards)))
	fields = ["card", "color", "type", "usd", "eur", "used"]
	pricedata = False
	if pricedata:
		print("Obteniendo precios de {} staples".format(len(staples)))
		fields.append("price_E")
		pricedata_eu = getMinEuroPrice(staples)
	for arch in archetypes:
		fields.append(arch["name"])
	# montar objeto final
	finalobj = []
	for dbcard in dbcards:
		c = {
			"card": dbcard["name"],
			"color": dbcard["color"],
			"type": dbcard["type"],
			"usd": "{}".format(dbcard["usd"]).replace(".", ","),
			"eur": "{}".format(dbcard["eur"]).replace(".", ","),
			"used": 0
		}
		if pricedata:
			dbcard["price_E"] = "{}".format(pricedata_eu[dbcard["name"]]).replace(".", ",")
		for arch in archetypes:
			if arch["name"] in staples[dbcard["name"]]:
				c[arch["name"]] = "{:.0%}".format(staples[dbcard["name"]][arch["name"]] / len(arch["decks"]))
				c["used"] += 1
			else:
				c[arch["name"]] = 0
		finalobj.append(c)
	with open("output/mtgtop8_{}_staples.csv".format(theformat), "w", newline='\n') as f:
		writer = csv.DictWriter(f, fieldnames=fields, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
		writer.writeheader()
		for c in finalobj:
			writer.writerow(c)
# MAIN
doSearch()
clasificarDecksPorArquetipos()
obtenerStaples()
escribirCSV()
