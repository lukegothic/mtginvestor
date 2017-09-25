import threading
from queue import Queue
import time
from lxml import html
import requests
import re
import math
import os

class Card:
	def __init__(self, id=0, cash=0, credit=0, foil=False):
		self.id = id
		self.cash = cash
		self.credit = credit
		self.foil = foil

def getCards(page):
	cards = []
	tree = html.fromstring(page)
	cardshtml = tree.xpath("//div[contains(@class,'itemContentWrapper')]")
	for cardhtml in cardshtml:
		foil = len(cardhtml.xpath(".//div[@class='foil']")) > 0
		pricewrapper = cardhtml.xpath(".//span[@class='stylePrice']")
		if len(pricewrapper) == 1:
			pricewrapper = pricewrapper[0]
			id = pricewrapper.xpath('.//form/input[@class="product_id"]')[0].attrib["value"];
			cash = "{}.{}".format(pricewrapper.xpath(".//div[@class='usdSellPrice']/span[@class='sellDollarAmount']")[0].text_content().replace(",",""), pricewrapper.xpath(".//div[@class='usdSellPrice']/span[@class='sellCentsAmount']")[0].text_content())
			credit = "{}.{}".format(pricewrapper.xpath(".//div[@class='creditSellPrice']/span[@class='sellDollarAmount']")[0].text_content().replace(",",""), pricewrapper.xpath(".//div[@class='creditSellPrice']/span[@class='sellCentsAmount']")[0].text_content())
			cards.append(Card(id, cash, credit, foil))
		else:
			print("premium")
			# es una premium card de las que hay que preguntar precio
	return cards

lock = threading.Lock()

cachedir = 'cache/ck/_buylist'
buylistfile = "{}/buylist.sql".format(cachedir)
baseurl = "http://www.cardkingdom.com/purchasing/mtg_singles?filter%5Bipp%5D=100&filter%5Bsort%5D=edition&filter%5Bsearch%5D=mtg_advanced&filter%5Bname%5D=&filter%5Bcategory_id%5D=0&filter%5Bfoil%5D=1&filter%5Bnonfoil%5D=1&filter%5Bprice_op%5D=%3E%3D&filter%5Bprice%5D=0.25&page="

def do_work(page):
	print("Page {}".format(page))

	cachefilename = "{}/{}.html".format(cachedir, page)

	try:
		f = open(cachefilename, "r", encoding="utf8")
		#TODO: invalidar cache si ha pasado 1 dia os.path.getmtime(path)
		data = f.read()
		f.close()
	except IOError:
		page = requests.get("{}{}".format(baseurl, page))
		data = page.text
		f = open(cachefilename, "w", encoding="utf8")
		f.write(data)
		f.close()
	cards = getCards(data)

	with lock:
		f = open(buylistfile, "a", encoding="utf8")
		for card in cards:
			f.write("({},{},{},{}),".format(card.id, card.cash, card.credit, card.foil))
		f.close()
		f.close()
def worker():
	while True:
		item = q.get()
		do_work(item)
		q.task_done()

def createStructure():
	if not os.path.exists(cachedir):
		os.makedirs(cachedir)
	f =	open(buylistfile, "w", encoding="utf8")
	f.write("INSERT INTO ck_buylist(card,cash,credit,foil) VALUES")
	f.close()

q = Queue()
for i in range(10):
	t = threading.Thread(target=worker)
	t.daemon = True
	t.start()

start = time.perf_counter()

createStructure();
for p in range(1, 138):
	q.put(p)

q.join()

print('time:',time.perf_counter() - start)

#select ck.code, ck.name, ck.price as ck, mkm.price as mkm, (ck.price - mkm.price) as pricediff, (ck.price/mkm.price) as pct from
#(select c.name, e.code, credit*0.91 as price, foil from ck_buylist buy left join ck_cards c on buy.card = c.id left join editions e on c.edition = e.code_ck where credit*0.91> 3) ck
#left join
#(select replace(replace(replace(replace(c.card,'+',' '), '%27', ''''),'%C3%86','AE'),'%2C',',') as name, e.code, (min(price) + 1.5) as price, foil from mkm_cardprices c left join editions e on c.edition = e.code_mkm group by c.card, e.code, foil) mkm
#on ck.name = mkm.name and ck.code = mkm.code and ck.foil = mkm.foil
#order by (ck.price - mkm.price) desc
