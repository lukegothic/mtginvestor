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

cachedir = "cache/mtgtop8/cmddecks"
types = { "LIST": "{}/lists".format(cachedir), "DETAIL": "{}/details".format(cachedir) }

if not os.path.exists(cachedir):
	os.makedirs(types["LIST"])
	os.makedirs(types["DETAIL"])

fromdate = (datetime.date.today() - datetime.timedelta(6*365/12)).strftime("%d/%m/%Y")
postdata = { "format": "EDH", "compet_check[P]": 1, "compet_check[M]": 1, "compet_check[C]": 1, "date_start": fromdate }

dpp = 25
rDeck = "event\?e=(\d*)&d=(\d*)&f=EDH"

cards = []

lock = threading.Lock()

def do_work(p):
	print(p)
	if p["type"] == "LIST":
		cachefile = "{}/{}.html".format(types[p["type"]], p["data"])
	else:
		cachefile = "{}/{}.html".format(types[p["type"]], re.search(rDeck, p["data"]).group(2))

	try:
		f = codecs.open(cachefile, "r", "utf-8")
		data = f.read()
		f.close()
	except IOError:
		if p["type"] == "LIST":
			pd = copy.copy(postdata)
			pd["current_page"] = p["data"]
			page = requests.post("http://mtgtop8.com/search", pd)
		else:
			page = requests.get("http://mtgtop8.com/{}".format(p["data"]))
		data = page.text
		f = codecs.open(cachefile, "w", "utf-8")
		f.write(data)
		f.close()
	tree = html.fromstring(data)
	if p["type"] == "LIST":
		if p["data"] == 1:
			a = tree.xpath("//div[@class='w_title']")[0].text_content().replace(" decks matching", "")
			paget = math.ceil((int)(a) / dpp)
			for pagen in range(2, paget + 1):
				q.put({ "type": "LIST", "data": pagen })
		rows = tree.xpath("//tr[@class='hover_tr']/td[@class='S11']/a")
		for row in rows:
			q.put({ "type": "DETAIL", "data": row.attrib["href"] })
	else:
		rows = tree.xpath("//td[@class='G14']/div[@class='hover_tr']")
		with lock:
			f = open("mtgtop8.sql", "a")
			for row in rows:
				card = row.text_content().replace(" ", "#", 1).split("#")
				quantity = (int)(card[0])
				name = card[1].replace("'", "''")
				for i in range(quantity):
					cards.append(name)
				#f.write("UPDATE mtgtop8_staples SET quantity=quantity+{1} WHERE name='{0}';INSERT INTO mtgtop8_staples(name, quantity) SELECT '{0}', {1} WHERE NOT EXISTS (SELECT 1 FROM mtgtop8_staples WHERE name='{0}');\n".format(name, quantity))
			f.close()

def worker():
	while True:
		p = q.get()
		do_work(p)
		q.task_done()

start = time.perf_counter()
q = Queue()
for i in range(6):
	t = threading.Thread(target=worker)
	t.daemon = True
	t.start()
q.put({ "type": "LIST", "data": 1 })
q.join()

cards = {i:cards.count(i) for i in cards}
f = open("mtgtop8.sql", "w")
for card in cards:
	f.write("INSERT INTO mtgtop8_staples(name, quantity) SELECT '{0}', {1};\n".format(card, cards[card]))
f.close()

print('time:',time.perf_counter() - start)

#select chr(34)||trim(name)||chr(34)||':'||(quantity/2.0)||',' from mtgtop8_staples order by quantity desc
