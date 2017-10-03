from lxml import html
import requests
import re
import os
import threading
from queue import Queue
import time
import math
import copy
import sys

cachedir = "__mycache__/mkm/prices"

if not os.path.exists(cachedir):
	os.makedirs(cachedir)

# obtener expansiones a procesar
rootfile = cachedir + "/root.html"

try:
	f = open(rootfile, "r", encoding="utf8")
	data = f.read()
	f.close()
except IOError:
	page = requests.get("https://www.magiccardmarket.eu/Expansions")
	data = page.text
	f = open(rootfile, "w", encoding="utf8")
	f.write(data)
	f.close()

tree = html.fromstring(data)
alleditions = list(map(lambda e: e.attrib["href"].replace("/Expansions/", ""), tree.xpath("//a[@class='alphabeticExpansion']")))

def getEditions():
	if len(sys.argv) == 2:
		s = sys.argv[1]
	else:
		for e, edition in enumerate(alleditions):
			print("[{}] {}".format(e, edition))
		s = input("Seleccione # o intro para todas: ")
	if s != "":
		if s == "0":
			return []
		else:
			s = s.split(",")
			filterededitions = []
			for e in s:
				filterededitions.append(alleditions[(int)(e)])
			return filterededitions
	else:
		return alleditions

rCard = "https:\/\/www.magiccardmarket.eu\/Products\/Singles\/(.*?)\/(.*)#(.*)"
rEditionNotFirstPage = "https:\/\/www.magiccardmarket.eu\/Products\/Singles\/(.*?)\?resultsPage=(\d*)"
rEdition = "https:\/\/www.magiccardmarket.eu\/Products\/Singles\/(.*)"
rHash = "#.*"
rPPU = '\(PPU: (.*?)\)'
reItemLocation = "'Item location: (.*)'"

cpp = 30
productFilter = { "productFilter[sellerRatings][]": ["1", "2"], "productFilter[idLanguage][]": [1], "productFilter[condition][]": ["MT", "NM"] }

lock = threading.Lock()

# comenzar a procesar expansiones
def do_work(url):
	print(url)
	# detectar tipo de peticion
	m = re.match(rCard, url)
	if m is None:
		# procesar edition
		m = re.match(rEditionNotFirstPage, url)
		if m is None:
			# procesar primera pagina
			m = re.match(rEdition, url)
			page = 1
		else:
			page = (int)(m.group(2)) + 1

		edition = m.group(1)
		editiondir = "{}/{}".format(cachedir, edition)

		editionpagecache = "{}/{}.html".format(editiondir, page)
		try:
			f = open(editionpagecache, "r", encoding="utf8")
			data = f.read()
			f.close()
		except IOError:
			resp = requests.get("{}{}sortBy=number&sortDir=asc&view=list".format(url, "?" if page == 1 else "&"))
			data = resp.text
			with lock:
				f = open(editionpagecache, "w", encoding="utf8")
				f.write(data)
				f.close()

		tree = html.fromstring(data)
		if page == 1:
			# procesar resto de paginas de la edicion
			total = tree.xpath("//span[@id='hitCountTop']/text()")
			if len(total) == 1:
				total = math.ceil((int)(total[0]) / cpp)
				for pagen in range(2, total + 1):
					q.put("{}?resultsPage={}".format(url, pagen - 1))
		# procesar cartas
		cards = tree.xpath("//table[contains(@class,'MKMTable')]/tbody/tr");
		with lock:
			f = open("{}/cards.sql".format(editiondir), "a", encoding="utf8")
			for card in cards:
				cardlinkelement = card.xpath("./td[3]/a")[0]
				cardurl = "https://www.magiccardmarket.eu{}".format(cardlinkelement.attrib["href"])
				cardcode = cardurl[cardurl.rfind("/")+1:]
				cardname = cardlinkelement.text_content().replace("'","''")
				q.put(cardurl + "#normal")
				cardfoilp = card.xpath("./td[7]/div/text()")
				if len(cardfoilp) == 1:
					cardfoilp = cardfoilp[0]
					if cardfoilp != "N/A":
						q.put(cardurl + "#foil")
				f.write("('{}','{}','{}'),".format(cardcode,cardname,edition))
			f.close()
	else:
		# procesar carta
		card = m.group(2)
		edition = m.group(1)
		editiondir = "{}/{}".format(cachedir, edition)
		foil = True if m.group(3) == "foil" else False
		carddir = "{}/{}/{}".format(cachedir, edition, card)
		if not os.path.exists(carddir):
			with lock:
				os.makedirs(carddir)

		cardpagecache = "{}/{}.html".format(carddir, m.group(3))

		try:
			f = open(cardpagecache, "r", encoding="utf8")
			data = f.read()
			f.close()
		except IOError:
			if foil:
				filter = copy.copy(productFilter)
				filter["productFilter[isFoil]"] = "Y"
			else:
				filter = productFilter
			resp = requests.post(re.sub(rHash, "", url), filter)
			data = resp.text
			if data != "":
				with lock:
					f = open(cardpagecache, "w", encoding="utf8")
					f.write(data)
					f.close()
			else:
				q.put(url)

		if data != "":
			tree = html.fromstring(data)
			with lock:
				f = open("{}/prices.sql".format(editiondir), "a", encoding="utf8")
				for row in tree.xpath('//tbody[@id="articlesTable"]/tr[not(@class)]'):
					itemlocation = row.xpath(".//td[@class='Seller']/span/span/span[@class='icon']")[0].attrib["onmouseover"]
					itemlocation = re.search(reItemLocation, itemlocation).group(1)
					seller = row.xpath(".//td[@class='Seller']/span/span/a")[0].attrib["href"].replace("/Users/", "")
					price = row.xpath(".//td[contains(@class,'st_price')]")[0].text_content().replace(",",".").replace("€","")
					available = row.xpath(".//td[contains(@class,'st_ItemCount')]")[0].text_content()
					ppu = re.search(rPPU, price)
					if not ppu is None:
						price = ppu.group(1)
						available = "4"
					f.write("('{}','{}',{},{},{},'{}','{}'),".format(card, edition, "true" if foil else "false", price, available, seller, itemlocation))
				f.close()

q = Queue()

def worker():
	while True:
		item = q.get()
		do_work(item)
		q.task_done()

def createStructure(edition):
	editiondir = "{}/{}".format(cachedir, edition)
	cardsfile = "{}/{}".format(editiondir, "cards.sql")
	pricesfile = "{}/{}".format(editiondir, "prices.sql")
	if not os.path.exists(editiondir):
		with lock:
			os.makedirs(editiondir)
	f = open(cardsfile, "w", encoding="utf8")
	f.write("INSERT INTO mkm_cards(code,name,edition) VALUES")
	f.close()
	f =	open(pricesfile, "w", encoding="utf8")
	f.write("INSERT INTO mkm_cardprices(card,edition,foil,price,available,seller,itemlocation) VALUES")
	f.close()

for i in range(6):
	t = threading.Thread(target=worker)
	t.daemon = True
	t.start()

while True:
	editions = getEditions()
	if len(editions) > 0:
		start = time.perf_counter()
		for edition in editions:
			createStructure(edition)
			q.put("https://www.magiccardmarket.eu/Products/Singles/" + edition)
		q.join()
		print('time:',time.perf_counter() - start)
	else:
		break
